from treys import Evaluator, Card, Deck
from poker.models.game import Game
from poker.models.hand_score import HandScore
import random
from poker.config import SB, BB, ranks, suits
import numpy as np


class StrategicAnalyst:

    def __init__(self):
        self.evaluator = Evaluator()
        self.game = None
        self.state = None

    def get_action(self, game):
        self.game = game
        self.state = game.states[-1]
        self.set_hand_strength()
        win_rate = self.eval_win_rate()
        game.states[-1].win_rate = win_rate
        if self.state.call > 0:
            call_ev = round(self.state.pot * win_rate - (1 - win_rate) * self.state.call, 4)
            print('strength:{}'.format(self.state.strength), 'win_rate:{}'.format(win_rate), 'call_ev:{}'.format(call_ev))
            if call_ev < 0 or win_rate < 0.33:
                return 'fold', 0
            elif call_ev > 0:
                if win_rate > 0.7:
                    return ('call', 0) if random.randint(1, 100) > (win_rate * 100) else ('raise', random.randint(1, 3))
                else:
                    return ('call', 0) if random.randint(1, 100) < (win_rate * 100) else ('raise', random.randint(0, 1))
        else:
            print('strength:{}'.format(self.state.strength), 'win_rate:{}'.format(win_rate), 'pot:{}'.format(self.state.pot))
            if win_rate < 0.45:
                return 'check', 0
            elif win_rate > 0.7:
                return ('check', 0) if random.randint(1, 100) > (win_rate * 100) else ('raise', random.randint(1, 5))
            else:
                return ('check', 0) if random.randint(50, 100) > (win_rate * 100) else ('raise', random.randint(1, 3))

    def set_hand_strength(self):
        if self.state.stage == 0:
            self.state.strength = HandScore.get_score(self.state.hand[0], self.state.hand[1])
            self.__pre_flop_ranges()
        else:
            wins = 0
            total = 0
            self_hand = [Card.new(self.state.hand[0]), Card.new(self.state.hand[1])]
            self_board = [Card.new(v) for v in self.state.board]
            opponent_ranges = self.game.opponent_pre_flop_ranges
            for _ in range(5000):
                try:
                    used_card = self_hand + self_board
                    # 底牌范围中随机抽取一手牌
                    opponent_cards = opponent_ranges[np.random.randint(0, len(opponent_ranges))]
                    opponent_hand = [Card.new(opponent_cards[0:2]), Card.new(opponent_cards[2:4])]
                    # 跳过重叠的牌
                    if opponent_hand[0] in used_card or opponent_hand[1] in used_card:
                        continue
                    # 洗牌
                    deck = Deck()
                    # 从牌堆中移除已出现的牌
                    used_card = used_card + opponent_hand
                    for card in used_card:
                        if deck.cards.__contains__(card):
                            deck.cards.remove(card)
                    board = self_board + deck.draw(5 - len(self_board))
                    # print(board)
                    # 计算牌力
                    strength1 = self.evaluator.evaluate(self_hand, board)
                    strength2 = self.evaluator.evaluate(opponent_hand, board)
                    total += 1
                    if strength1 < strength2:  # 修正：较大的值表示较弱的牌
                        wins += 1
                except Exception as e:
                    print('Error in win rate calculation:', str(e))
            self.state.strength = round(wins / total, 4)

    def eval_win_rate(self):
        """根據手牌強度，計算獲勝概率
        #  贏率降低的條件有：入池人數越多、牌面越濕、玩家存在c-bet，check-raise等行為
        """
        strength = self.state.strength
        if strength > 0.8:
            return strength
        reduce_rate = 1
        active_size = 0
        raise_size = 0
        for player in self.state.players:
            if player.active == 1:
                active_size += 1
                if player.action == 'raise':
                    raise_size += 1
        if active_size > 2:
            reduce_rate = reduce_rate * 0.9
        if raise_size > 1:
            reduce_rate = reduce_rate * 0.9
        if self.state.stage == 0:
            reduce_rate = reduce_rate * (1 - self.state.pot/(15 * BB))
        return round(strength * reduce_rate, 4)

    def __pre_flop_action(self):
        position = self.state.position
        pot = self.state.pot
        call = self.state.call
        score = HandScore.get_score(self.state.hand[0], self.state.hand[1])
        self.state.win_rate = score
        call_ev = round(pot * score - (1 - score) * call, 4)
        print('win_rate:{}'.format(score), 'pot:{}'.format(pot), 'call_ev:{}'.format(call_ev))
        if score >= 0.8:
            # 超强牌，造大底池ii
            if pot < 4 * BB:
                return 'raise', random.randint(2, 4)
            return 'raise', random.randint(3, 6)
        elif 0.8 > score >= 0.7:
            # 强牌，控制底池到合适的大小
            if call > 3 * BB:
                return 'call', 0
            return 'raise', random.randint(2, 4)
        elif 0.7 > score >= 0.6:
            # 中强牌，控制底池，避免参与过大的底池
            if call < 2 * BB:
                return 'raise', random.randint(1, 2)
            if 2 * BB <= call <= 10 * BB and call_ev > 0:
                return 'call', 0
            if call_ev == 0 and position == 6 and random.randint(1, 3) == 1:
                return 'raise', random.randint(1, 2)
        elif 0.6 > score >= 0.55:
            # 中等牌，避免参与过大的底池
            if pot < 30 * BB:
                if call_ev > 0:
                    return 'call', 0
                if call_ev == 0 and position == 6 and random.randint(1, 3) == 1:
                    return 'raise', random.randint(1, 2)
        elif 0.55 > score >= 0.5:
            # 弱牌，小底池有位置可参与
            if pot < 20 * BB and position in (1, 2, 5, 6) and call_ev > 0 and random.randint(1, 3) == 1:
                return 'call', 0
        return 'fold', 0

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
