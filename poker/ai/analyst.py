from treys import Evaluator, Card, Deck
from poker.models.card import basic_strength,eval_strength,wet_board
from poker.models.card import HandScore
import random
from poker.config import SB, BB, ranks, suits
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

    def get_action(self, game):
        self.game = game
        self.state = game.states[-1]
        # self.__hand_strength()
        self.__win_rate()
        self.__calculate_ev()
        if self.state.stage == 0:
            self.__pre_flop_action()
            self.__pre_flop_ranges()
        else:
            self.__flop_action()

        print('hand_strength:{},win_rate{},call_ev:{},raise_ev:{},action:{}'.format(
            self.state.strength, self.state.win_rate,
            self.state.call_ev, self.state.raise_ev, self.state.action))

        return self.state.action

        # if self.state.call > 0:
        #     call_ev = round(self.state.pot * win_rate - (1 - win_rate) * self.state.call, 4)
        #     print('strength:{}'.format(self.state.strength), 'win_rate:{}'.format(win_rate), 'call_ev:{}'.format(call_ev))
        #     if call_ev < 0 or win_rate < 0.33:
        #         return 'fold', 0
        #     elif call_ev > 0:
        #         if win_rate > 0.7:
        #             return ('call', 0) if random.randint(1, 100) > (win_rate * 100) else ('raise', random.randint(1, 3))
        #         else:
        #             return ('call', 0) if random.randint(1, 100) < (win_rate * 100) else ('raise', random.randint(0, 1))
        # else:
        #     print('strength:{}'.format(self.state.strength), 'win_rate:{}'.format(win_rate), 'pot:{}'.format(self.state.pot))
        #     if win_rate < 0.45:
        #         return 'check', 0
        #     elif win_rate > 0.7:
        #         return ('check', 0) if random.randint(1, 100) > (win_rate * 100) else ('raise', random.randint(1, 5))
        #     else:
        #         return ('check', 0) if random.randint(50, 100) > (win_rate * 100) else ('raise', random.randint(1, 3))

    def __hand_strength(self):
        """
        仅从牌面角度考虑手牌强度
        :return:
        """
        if self.state.stage == 0:
            self.state.strength = HandScore.get_score(self.state.hand[0], self.state.hand[1])
        else:
            self.state.strength = eval_strength(self.state.hand, self.state.board, self.game.opponent_pre_flop_ranges)

            # basic = basic_strength(self.state.hand, self.state.board)
            # equity =
            # wetness = wet_board(self.state.board)
            # potential = min(equity * (1 + wetness), 1.0)
            #     (
            #         0.4 * basic +  # 当前强度（归一化）
            #         0.3 * equity +  # 实际胜率
            #         0.3 * potential  # 发展潜力
            # ))

    def __win_rate(self):
        """根據手牌強度，計算獲勝概率
        #  贏率降低的條件有：入池人數越多、牌面越濕、玩家存在c-bet，check-raise等行為
        """
        adjust_rate = 1
        pot = self.state.pot 
        if self.state.stage == 0:
            p_level=0 if pot<5*BB else 1 if pot<20*BB else 2
            strength = HandScore.get_score(self.state.hand[0], self.state.hand[1])
            # 翻牌前，调节赢率的变量：底池大小
            if strength>0.8:
                adjust_rate = 1.2 if p_level==1 else 1.1 if p_level==2 else 1
            elif strength>0.65:
                adjust_rate = 0.9 if p_level==1 else 0.8 if p_level==2 else 1
            else:
                adjust_rate = 0.8 if p_level==1 else 0.7 if p_level==2 else 1
        else:
            strength = eval_strength(self.state.hand, self.state.board, self.game.opponent_pre_flop_ranges)
            # 翻牌后，调节赢率的变量： 玩家的行为特征+牌面湿润度
            h_level =1.1 if no_raise() else 1 if no_cbet_tbet() else 0.9
            w_level=1 if no_pair() else 0.9 if one_pair() else 0.8
            if is_nuts():
                adjust_rate = 2
            else:
                adjust_rate = h_level * w_level
        self.state.strength = strength
        self.state.win_rate = round(strength * adjust_rate, 4)

    def __pre_flop_action(self):
        position = self.state.position
        call = self.state.call
        win_rate = self.state.win_rate
        if call>0:
            if self.state.call_ev<0:
                return 'fold',0
            else:
                # raise or call
                c_level=0 if call<BB*3 else 2 if call>10*BB else 1
                if win_rate>0.8:
                    return 'raise', random.randint(2, 4)
                elif win_rate>0.7:
                    if random.randint(1,100)<win_rate*100:
                        return 'raise', random.randint(2, 4)
                    else:
                        return 'call',0
                elif win_rate>0.6:
                    if c_level =2:
                        if random.randint(1,100)<win_rate*100:
                            return 'call', 0
                        else:
                            return 'fold', 0
                    else:
                        return 'call', 0
                else win_rate>0.5:
                    if c_level =2:
                        return 'fold', 0
                    elif position >4 or c_level=0:
                        return 'call', 0
                    else:
                        return 'fold', 0
                else:
                    return 'fold', 0
        else:
            if self.state.raise_ev<BB:
                return 'check', 0
            else:
                if win_rate>0.8:
                    return 'raise', random.randint(2, 4)
                elif win_rate>0.55:
                    if random.randint(1,100)<win_rate*100:
                        return 'raise', random.randint(1, 3)
                    else:
                        return 'check', 0
                else:
                    return 'check', 0

    def __flop_action(self):
        # 风险调整系数
        bankroll_factor = min(self.state.stack / 100*BB, 1.5)
        # 特殊情况处理
        if self.state.call == 0:
            final_ev['check'] = ev_matrix['call']
            # del final_ev['call']

        # 选择最优动作
        best_action = max(final_ev, key=final_ev.get)

        if best_action == 'raise' and win_rate > 0.60 and random.randint(1, 100) > (win_rate * 100):
            raise_size = int(final_ev[best_action] / BB)
            return 'raise', random.randint(0, min(raise_size, 5))
        elif final_ev['call'] > 0 and win_rate > 0.5:
            return 'call', 0
        return 'fold' if self.state.call > 0 else 'check', 0

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
        if self.game.opponent_pre_flop_ranges:
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
        self.game.opponent_pre_flop_ranges = HandScore.get_ranges(min_score, max_score)

    def __calculate_ev(self):
        """计算各动作的期望值"""
        ev_matrix = {}

        to_call = self.state.call
        pot = self.state.pot
        equity = self.state.win_rate
        players = 1
        for p in self.state.players:
            players += 1 if p.active == 1 else 0

        # 基本赔率计算
        # pot_odds = to_call / pot + to_call
        # implied_odds = 1.5  # 隐含赔率估计值

        # 核心决策因子
        decision_factor = round(
                equity * self.position_weights[self.state.position] *
                self.stage_factors[self.state.stage] *
                (1 + 0.1 * (players - 2)), 4
        )

        # Fold EV（固定为0）
        self.state.fold_ev = 0

        # Check/Call EV
        self.state.call_ev = round((equity * pot - (1 - equity) * to_call) * decision_factor, 4)

        # Raise EV（动态计算最佳加注量）
        raise_ranges = self._get_raise_ranges()
        best_raise = {'amount': 0, 'ev': -np.inf}

        for ratio in raise_ranges:
            raise_amount = pot * ratio
            fold_prob = self._estimate_fold_prob(raise_amount)

            ev = round((fold_prob * pot +
                        (1 - fold_prob) * (equity * pot + raise_amount) -
                        (1 - equity) * (to_call + raise_amount)), 4)

            if ev > best_raise['ev']:
                best_raise = {'amount': raise_amount, 'ev': ev}

        self.state.raise_ev = best_raise

    def _get_raise_ranges(self):
        """动态生成加注范围"""
        # 基础加注尺度
        if self.state.stage == 0:
            base_ranges = [0.5, 0.75, 1.0]
        elif 0 < self.state.stage < 3:
            base_ranges = [0.67, 0.8, 1.0]
        else:  # river
            base_ranges = [0.5, 0.75, 1.0, 1.25]

        raise_times = 0
        active_players = [p.name if p.active == 1 else None for p in self.state.players]
        for ste in self.game.states:
            for p in ste.players:
                if p.name in active_players and p.action == 'raise' and p.amount > 2*BB:
                    raise_times += 1

        # 根据对手倾向调整
        # if params['vpip'] > 0.35:
        if raise_times > 3:
            base_ranges = [round(r * 0.8, 2) for r in base_ranges]
        if raise_times < 2:
            base_ranges = [round(r * 1.2, 2) for r in base_ranges]
        return base_ranges

    def _estimate_fold_prob(self, raise_amount):
        """估计对手弃牌概率"""
        base_prob = 0.3
        # 加注量影响
        base_prob += min((raise_amount / self.state.pot) * 0.2, 0.4)

        raise_times = 0
        active_players = [p.name if p.active == 1 else None for p in self.state.players]
        for ste in self.game.states:
            for p in ste.players:
                if p.name in active_players and p.action == 'raise' and p.amount > 2*BB:
                    raise_times += 1

        # 对手倾向调整
        # if raise_times > 2:
        #     base_prob = base_prob * 0.9
        # if raise_times < 2:
        #     base_prob = base_prob * 1.1
        if len(active_players) > 1 or raise_times > 1:
            return 0.1
        else:
            return 0.2
        # return float(np.clip(base_prob, 0.1, 0.8))

    def _player_analyze(self):
        active_numbers = 1  # 入池人数
        raise_times = 0     # 加注次数
        c_bet_times = 0     # 持续下注次数
        for player in self.state.players:
            if player.active == 1:
                active_numbers += 1
                if player.action == 'raise':
                    raise_times += 1
        if len(self.game.states) > 1:
            pre_state = self.game.states[-2]
            


