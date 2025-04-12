from treys import Evaluator, Card, Deck
from models.card import basic_strength, eval_strength, wet_board
from models.card import HandScore
import random
from config import SB, BB, ranks, suits
import numpy as np


class StrategicAnalyst:

    def __init__(self):
        self.evaluator = Evaluator()
        self.game = None
        self.state = None
        self.position_weights = {
            6: 1.2, 1: 0.8, 2: 0.9,
            3: 1.0, 4: 1.1, 5: 1.15
        }
        self.stage_factors = {
            0: 0.7, 1: 1.0,
            2: 1.2, 3: 1.5
        }

    def calculate_action(self, game):
        self.game = game
        self.state = game.states[-1]

        call = self.state.call
        win_rate = self.__win_rate()
        call_ev = round((win_rate * self.state.pot - (1 - win_rate) * call), 4)
        self.state.call_ev = call_ev

        best_raise = self.__raise_ev()
        raise_ratio, raise_amount, raise_ev = best_raise['ratio'], best_raise['amount'], best_raise['ev']
        self.state.raise_ev = raise_ev

        if call > 0:
            if call_ev < SB:
                self.state.action, self.state.bet = 'fold', 0
            elif raise_ev > 0 and random.random() < win_rate > random.uniform(0.65, 0.75):
                # 胜率较大的情况下，大概1/4机会加注
                self.state.action, self.state.bet = 'raise', random.randint(1, 3)
            else:
                self.state.action, self.state.bet = 'call', 0
        else:
            if raise_ev > 0 and random.uniform(0.33, 0.99) < win_rate > random.uniform(0.6, 0.75):
                # 胜率较大的情况下，大概1/2机会主动出击
                self.state.action, self.state.bet = 'bet', random.randint(1, 3)
            else:
                self.state.action, self.state.bet = 'check', 0

        print('hand_strength:{},win_rate{},call_ev:{},raise_ev:{},action:{},bet:{}'.format(
            self.state.strength, self.state.win_rate,
            self.state.call_ev, self.state.raise_ev, self.state.action, self.state.bet))
        return self.state.action, self.state.bet

    def __win_rate(self):
        """根據手牌強度，計算獲勝概率
        #  贏率降低的條件有：入池人數越多、牌面越濕、玩家存在c-bet，check-raise等行為
        """
        stage = self.state.stage
        if stage == 0:
            self.state.strength = HandScore.get_score(self.state.hand[0], self.state.hand[1])
            self.__pre_flop_ranges()
            factor = self.__pre_flop_adjust_factor()
        else:
            self.state.strength = eval_strength(self.state.hand, self.state.board, self.game.opponent_ranges)
            factor = self.__aft_flop_adjust_factor()
        win_rate = round(self.state.strength * factor, 4)
        self.state.win_rate = win_rate
        return win_rate

    def __pre_flop_adjust_factor(self):
        """ 翻牌前胜率调节系数
            factor1：底池大小，底池越大，玩家手牌强度越大，赢率降低
            factor2: 入池人数，入池人数越多，赢率降低
        """
        pot = self.state.pot
        strength = self.state.strength
        p_level = 0 if pot < 5 * BB else 1 if pot < 20 * BB else 2
        p_numbers = len(self.state.players)
        if strength > 0.8:
            # 绝对强牌
            factor1 = 1.2 if p_level == 1 else 1.1 if p_level == 2 else 1
            factor2 = 1.1 if p_numbers < 3 else 0.9 if p_numbers > 3 else 1
        elif strength > 0.65:
            # 中强牌
            factor1 = 0.9 if p_level == 1 else 0.8 if p_level == 2 else 1
            factor2 = max(p_numbers*0.95, 0.85)
        elif strength > 0.5:
            # 一般牌
            factor1 = 0.9 if p_level == 1 else 0.75 if p_level == 2 else 1
            factor2 = min(p_numbers*0.9, 0.8)
        else:
            # 弱牌
            factor1 = 0.8 if p_level == 1 else 0.7 if p_level == 2 else 1
            factor2 = min(p_numbers*0.85, 0.75)
        return round(factor1 * factor2, 2)

    def __aft_flop_adjust_factor(self):
        """ 翻牌后调节系数
            factor1：玩家下注尺度。下注尺度越大，成牌概率越大，赢率降低
            factor2：牌面湿润度。 牌面越湿润，难度越大，赢率降低
            factor3：玩家下注行为。 玩家持续下注，有强牌概率越大，赢率降低
        """
        is_c_bet = self._is_c_bet()    # 持续下注
        is_b_bet = self._is_b_bet()    # 大注
        is_flop_raise = self._is_flop_raise()   # 翻牌后加注
        is_nuts = self._is_nuts()     # 拿到坚果
        wet_level = 1

        if is_nuts:
            return 2
        else:
            p_numbers = len(self.state.players)     # 入池人数
            factor1 = 1 if p_numbers < 2 else 0.8 if p_numbers > 2 or self.state.stage > 1 else 0.9
            factor2 = 0.9 if is_c_bet else 1
            factor3 = 0.9 if is_b_bet else 1
            factor4 = 0.9 if is_flop_raise else 1
            factor5 = 0.9 if wet_level == 1 else 0.8 if wet_level == 2 else 1
            return round(factor1 * factor2 * factor3 * factor4 * factor5, 2)

    def __pre_flop_ranges(self):
        """
        翻牌前手牌范围评估。
        翻牌前的手牌范围。跟底池大小、玩家行为有关。
        player_pre_act = 'raise、call、3bet、check'  # 翻牌前行动。加注通常表示较强的手牌，而跟注可能意味着中等或投机性手牌。
        player_flop_act = '持续bet、check-raise'  # 翻牌后行动。
        player_balance = 100  # 筹码量。 短筹码玩家倾向于玩得更紧，而深筹码玩家可能更激进，尝试利用筹码优势进行诈唬或价值下注。
        player_amt = 6  # 翻牌后下注尺度。大额下注通常表示强牌或诈唬,小额下注可能意味着中等牌力或试探性下注
        player_style = '0, 1, 2'  # 历史行为。 紧凶、松凶、被动。紧凶玩家加注时通常有强牌，而松凶玩家可能用更宽的范围加注
        board_style = '单张成顺、单张成花、卡顺、三张花、'  # 牌面结构。 湿润牌面下注，对手可能有更多听牌或成牌
        :return:
        """
        if self.game.opponent_ranges:
            return
        state0 = None
        for i in range(len(self.game.states)):
            if self.game.states[i].stage == 0:
                state0 = self.game.states[i]
        pot_bb = int(state0.pot / BB)
        active_size = 0
        raise_size = 0
        for player in state0.players:
            if player.active == 1:
                active_size += 1
                if player.action == 'raise':
                    raise_size += 1
        if pot_bb > 50:
            if active_size > 1:
                min_score, max_score = 0.6, 0.9
            else:
                min_score, max_score = 0.65, 0.9
        elif 20 < pot_bb <= 50:
            min_score, max_score = 0.5, 0.9
        elif 10 < pot_bb <= 20:
            if active_size > 1:
                min_score, max_score = 0.4, 0.7
            else:
                min_score, max_score = 0.4, 0.8
        else:
            if active_size > 1:
                min_score, max_score = 0.4, 0.7
            else:
                min_score, max_score = 0.2, 0.9
        self.game.opponent_ranges = HandScore.get_ranges(min_score, max_score)

    def __raise_ev(self):
        """计算各动作的期望值"""
        to_call = self.state.call
        pot = self.state.pot
        equity = self.state.win_rate

        # 加注量，相对底池占比
        raise_ranges = [0.3, 0.5, 0.65, 0.8, 1.0, 1.25]
        best_raise = {'amount': 0, 'ev': -1}
        for ratio in raise_ranges:
            raise_amount = pot * ratio
            fold_prob = self._estimate_fold_prob(raise_amount)

            ev = round((fold_prob * pot +
                        (1 - fold_prob) * (equity * pot + raise_amount) -
                        (1 - equity) * (to_call + raise_amount)), 4)

            if ev > best_raise['ev']:
                best_raise = {'ratio': ratio, 'amount': raise_amount, 'ev': ev}

        return best_raise

    def _estimate_fold_prob(self, raise_amount):
        """玩家弃牌概率"""
        # 加注量影响
        base_prob = min((raise_amount / self.state.pot) * 0.2, 0.3)
        if self.state.stage == 0:
            active_numbers = len(self.state.players)
            fold_prob = round(base_prob / active_numbers, 2)
        else:
            raise_times = 0
            active_players = [p.name if p.active == 1 else None for p in self.state.players]
            for ste in self.game.states:
                for p in ste.players:
                    if p.name in active_players and p.action == 'raise' and p.amount > 2 * BB:
                        raise_times += 1
            fold_prob = round(base_prob / raise_times, 2)
        return fold_prob

    def _player_analyze(self):
        active_numbers = 1  # 入池人数
        raise_times = 0  # 加注次数
        c_bet_times = 0  # 持续下注次数
        for player in self.state.players:
            if player.active == 1:
                active_numbers += 1
                if player.action == 'raise':
                    raise_times += 1
        if len(self.game.states) > 1:
            pre_state = self.game.states[-2]

    def _is_c_bet(self):
        for sta in self.game.states:
            pls = sta.players
            # todo

        return False

    def _is_b_bet(self):
        pot = self.state.pot
        for sta in self.game.states:
            pls = sta.players
            # todo

        return False

    def _is_flop_raise(self):
        pot = self.state.pot
        for sta in self.game.states:
            pls = sta.players
            # todo

        return False

    def _is_nuts(self):

        return False

