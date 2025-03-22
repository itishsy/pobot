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
        if self.state.stage == 0:
            return self.__pre_flop_action()
        else:
            win_rate = self.eval_win_rate()
            raise_amt = self.state.pot * win_rate / (1 - win_rate)
            print('win_rate:{}'.format(win_rate), 'raise_amt:{}'.format(raise_amt))
            if raise_amt >= self.state.call:
                raise_num = int(raise_amt/self.state.call)
                if raise_num == 0:
                    return 'call', 0
                # 随机选择raise或check。
                if random.randint(1, 100) > (win_rate * 100):
                    return 'raise', random.randint(1, raise_num)
                else:
                    return 'call', 0
            else:
                if self.state.call == 0:
                    return 'check', 0
                return 'fold', 0

    def eval_win_rate(self, num_simulations=5000):
        wins = 0
        total = 0
        ranges = self.__pre_flop_ranges()
        self_hand = [Card.new(self.state.hand[0]), Card.new(self.state.hand[1])]
        self_board = [Card.new(v) for v in self.state.board]
        for _ in range(num_simulations):
            try:
                # 底牌范围中随机抽取一手牌
                opponent_cards = ranges[np.random.randint(0, len(ranges))]
                opponent_hand = [Card.new(opponent_cards[0:2]), Card.new(opponent_cards[2:4])]

                # 跳过重叠的牌
                if (opponent_hand[0] == self.state.hand[0] or opponent_hand[0] == self.state.hand[1] or
                        opponent_hand[1] == self.state.hand[0] or opponent_hand[1] == self.state.hand[1]):
                    continue

                # 洗牌
                deck = Deck()
                # 从牌堆中移除已出现的牌
                used_card = self_hand + opponent_hand + self_board
                for card in used_card:
                    if deck.cards.__contains__(card):
                        deck.cards.remove(card)

                board = self_board + deck.draw(5 - len(self_board))
                # 计算牌力
                strength1 = self.evaluator.evaluate(self_hand, board)
                strength2 = self.evaluator.evaluate(opponent_hand, board)
                
                total += 1
                if strength1 < strength2:  # 修正：较大的值表示较弱的牌
                    wins += 1
            except Exception as e:
                print('Error in win rate calculation:', str(e))
                continue
                
        return wins / total if total > 0 else 0.5  # 添加安全检查

    def __pre_flop_action(self):
        position = self.state.position
        pot = self.state.pot
        call = self.state.call
        score = HandScore.get_score(self.state.hand[0], self.state.hand[1])
        call_ev = round(pot * score - (1 - score) * call, 4)
        print('hand score:{}'.format(score), 'pot:{}'.format(pot), 'call_ev:{}'.format(call_ev))
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
            if 2 * BB <= call <= 10 * BB or call_ev > 0:
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
        手牌范围。评估翻牌前的手牌范围。跟底池大小、玩家行为有关。
        player_pre_act = 'raise、call、3bet、check'  # 翻牌前行动。加注通常表示较强的手牌，而跟注可能意味着中等或投机性手牌。
        player_flop_act = '持续bet、check-raise'  # 翻牌后行动。
        player_balance = 100  # 筹码量。 短筹码玩家倾向于玩得更紧，而深筹码玩家可能更激进，尝试利用筹码优势进行诈唬或价值下注。
        player_amt = 6  # 翻牌后下注尺度。大额下注通常表示强牌或诈唬,小额下注可能意味着中等牌力或试探性下注
        player_style = '0, 1, 2'  # 历史行为。 紧凶、松凶、被动。紧凶玩家加注时通常有强牌，而松凶玩家可能用更宽的范围加注
        board_style = '单张成顺、单张成花、卡顺、三张花、'  # 牌面结构。 湿润牌面下注，对手可能有更多听牌或成牌
        :return:
        """
        pot_bb = 2
        for i in range(len(self.game.states)):
            if self.game.states[i].stage == 0:
                pot_bb = int(self.game.states[i].pot / BB)
        if 1 < pot_bb <= 3:
            return HandScore.get_ranges(0.2, 0.6)
        elif 3 < pot_bb <= 10:
            return HandScore.get_ranges(0.4, 0.9)
        elif 10 < pot_bb <= 50:
            return HandScore.get_ranges(0.5, 0.9)
        else:
            return HandScore.get_ranges(0.55, 0.9)

