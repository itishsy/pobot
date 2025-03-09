from treys import Card, Evaluator, Deck
import numpy as np
import random
from poker.config import BB
from itertools import combinations

suits = ['s', 'h', 'c', 'd']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']


def order_cards(card1, card2):
    rank1 = card1[:-1]
    rank2 = card2[:-1]
    if ranks.index(rank1) > ranks.index(rank2):
        return card1+card2
    else:
        return card2+card1


class Cards:

    def __init__(self):
        self.deck = [rank + suit for rank in ranks for suit in suits]

    Straight_Flush = 9000
    Four_Of_A_Kind = 8000
    Full_House = 7000
    Flush = 6000
    Straight = 5000
    Three_Of_A_Kind = 4000
    Two_Pair = 3000
    Pair = 2000
    High_Card = 1000

    def card_index(self, card):
        rank = card[:-1]
        return ranks.index(rank)

    def card_value(self, card):
        return self.card_index(card) + 2

    def lookup(self, board, hand):
        score = 0
        for combination in combinations(hand + board, 5):
            five_score = self.five_card(list(combination))
            if five_score > score:
                score = five_score
        return score

    def five_card(self, cards):
        # 先将牌按牌面数值大小排序
        sorted_cards = sorted(cards, key=self.card_index)

        # 获取牌面和花色列表
        ranks_list = [card[:-1] for card in sorted_cards]
        suits_list = [card[-1] for card in sorted_cards]

        # 判断是否同花顺
        is_straight = False
        is_flush = len(set(suits_list)) == 1
        straight_ranks = [ranks.index(rank) for rank in ranks_list]
        if max(straight_ranks) - min(straight_ranks) == 4 and len(set(straight_ranks)) == 5:
            is_straight = True
        if is_straight and is_flush:
            # 同花顺。 最大值为：9000+14=9014（A-T） 最小值：9000+2=9005（5-A）
            return self.Straight_Flush + self.card_value(sorted_cards[-1])

        # 判断是否四条
        rank_counts = {}
        for rank in ranks_list:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        for count in rank_counts.values():
            if count == 4:
                four_rank = [r for r in rank_counts if rank_counts[r] == 4][0]
                remaining_cards = [c for c in sorted_cards if c[:-1] != four_rank]
                # 四条。 最大值为：8000+140+13=8153（4条A+K） 最小值：8000+20+3=8023（4条2+3）
                return self.Four_Of_A_Kind + self.card_value(four_rank)*10 + self.card_value(remaining_cards[-1])

        # 判断是否葫芦（三条加一对）
        three_ranks = [r for r in rank_counts if rank_counts[r] == 3]
        two_ranks = [r for r in rank_counts if rank_counts[r] == 2]
        if three_ranks and two_ranks:
            # 葫芦。最大值为：7000+140+13=7153（3条A+2条K） 最小值：7000+20+3=7023（3条2+2条3）
            return self.Full_House + self.card_value(three_ranks[0])*10 + self.card_value(two_ranks[0])

        # 判断是否同花
        if is_flush:
            # 同花。 最大值为：6000+14=6014（A花） 最小值：6000+7=6007（7花）
            return self.Flush + self.card_value(sorted_cards[-1])

        # 判断是否顺子
        if is_straight:
            # 顺子。 最大值为：5000+14=5014（A顺） 最小值：5000+5=5005（5顺）
            return self.Straight + self.card_value(sorted_cards[-1])

        # 判断是否三条
        if 3 in rank_counts.values():
            three_rank = [r for r in rank_counts if rank_counts[r] == 3][0]
            remaining_cards = [c for c in sorted_cards if c[:-1] != three_rank]
            # 三条。 最大值为：4000+140+13=4153（三条A+K） 最小值：4000+20+4=4204（三条2+34）
            return self.Three_Of_A_Kind + self.card_value(three_rank)*10 + self.card_value(remaining_cards[-1])

        # 判断是否两对
        pair_count = 0
        pair_ranks = []
        for count in rank_counts.values():
            if count == 2:
                pair_count += 1
                pair_ranks.append([r for r in rank_counts if rank_counts[r] == 2])
        if pair_count == 2:
            c1 = self.card_value(pair_ranks[0][0])
            c2 = self.card_value(pair_ranks[0][1])
            # 两对。 最大值为：3000+140+13=3153（2条A+2条K） 最小值：3000+20+3=3203（三条2+三条3）
            return self.Two_Pair + max(c1, c2)*10 + min(c1, c2)

        # 判断是否一对
        if pair_count == 1:
            pair_rank = [r for r in rank_counts if rank_counts[r] == 2][0]
            remaining_cards = [c for c in sorted_cards if c[:-1] != pair_rank]
            # 两对。 最大值为：2000+140+13=2153（2条A+2条K） 最小值：2000+20+3=2023（三条2+三条3）
            return (self.Pair + self.card_value(pair_rank)*10 + self.card_value(remaining_cards[-1])
                    + self.card_value(remaining_cards[-2]))

        # 如果都不是，就是高牌
        # 高牌。 最大值为：1000+140+13+12+10
        return (self.High_Card + self.card_value(sorted_cards[-1]) * 10 +
                self.card_value(sorted_cards[-2]) + self.card_value(sorted_cards[-3])
                + self.card_value(sorted_cards[-4]))

    def five_card_name(self, cards):
        val = self.five_card(cards)
        m2 = val // 100 % 100 - 2   # 中间2位
        t2 = val % 100 - 2          # 最后2位
        if val >= self.Straight_Flush:
            s = '同花顺' + ranks[t2]
        elif val >= self.Four_Of_A_Kind:
            s = '四条' + ranks[m2] + ',' + ranks[t2]
        elif val >= self.Full_House:
            s = '葫芦' + ranks[m2] + ',' + ranks[t2]
        elif val >= self.Flush:
            s = '同花' + ranks[t2]
        elif val >= self.Straight:
            s = '顺子' + ranks[t2]
        elif val >= self.Three_Of_A_Kind:
            s = '三条' + ranks[m2] + ',' + ranks[t2]
        elif val >= self.Two_Pair:
            s = '两对' + ranks[m2] + ',' + ranks[t2]
        elif val >= self.Pair:
            s = '一对' + ranks[m2] + ',' + ranks[t2]
        else:
            s = ('高牌' + ranks[val // 1000 % 10 + 3] + ','
                 + ranks[val // 100 % 10 + 3] + ','
                 + ranks[val // 10 % 10 + 3] + ','
                 + ranks[val % 10 + 3])
        return s


class Hand:

    def __init__(self, card1, card2):
        self.evaluator = Evaluator()
        self.cards = Cards()
        self.hands = card1 + card2 if self.cards.card_value(card1) > self.cards.card_value(card2) else card2 + card1
        self.hand = [Card.new(card1),  Card.new(card2)]
        self.deck = Deck()
        self.board = []

    def add_board(self, card):
        # print('add board：', card)
        if card in self.cards.deck:
            # print('board append：', card)
            self.board.append(Card.new(card))

    def get_score(self):
        """ preFlop阶段取默认值。flop按如下组合强度，算法：(8000-strength)/8000 * 100
        同花顺     1-10
        四条	      11-166
        葫芦	      167-322
        同花	      323-1599
        顺子	      1600-1609
        三条	      1610-2467
        两对	      2468-3325
        一对	      3326-6185
        高牌	      6186-7462
        :return: 返回0-100之间的手牌得分
        """
        my_strength = self.evaluator.evaluate(self.hand, self.board)
        print('牌型名称:', self.print_class_name(my_strength))
        board_strength = -1
        if len(self.board) == 5:
            board_strength = self.evaluator.evaluate([], self.board)
        if board_strength == my_strength:
            return 49.99
        else:
            return (8000 - my_strength) / 80

    def stronger_range(self):
        cur_deck = Deck()
        known_cards = self.hand + self.board
        remaining_cards = [card for card in cur_deck.cards if card not in known_cards]
        my_strength = self.evaluator.evaluate(self.hand, self.board)
        # 遍历所有可能的手牌组合
        stronger_hands = set()
        for opponent_hand in combinations(remaining_cards, 2):
            sorted_hand = tuple(sorted(opponent_hand, reverse=True))
            # 计算对手手牌 + 公共牌的牌力
            opponent_strength = self.evaluator.evaluate(opponent_hand, self.board)

            # 如果对手的牌力更强，记录下来
            if opponent_strength < my_strength:
                stronger_hands.add(sorted_hand)
        return stronger_hands

    def win_rate(self, ranges):
        wins = 0
        num_simulations = 5000
        for _ in range(num_simulations):
            try:
                # 底牌范围中随机抽取一手牌
                opponent_cards = ranges[np.random.randint(0, len(ranges))]
                opponent_hand = [Card.new(opponent_cards[0:2]), Card.new(opponent_cards[2:4])]

                # 跳过重叠的牌
                if (opponent_hand[0] == self.hand[0] or opponent_hand[0] == self.hand[1] or
                        opponent_hand[1] == self.hand[0] or opponent_hand[1] == self.hand[1]):
                    continue

                # 洗牌
                self.deck.shuffle()
                # 从牌堆中移除已出现的牌
                used_card = self.hand + opponent_hand + self.board
                for card in used_card:
                    if self.deck.cards.__contains__(card):
                        self.deck.cards.remove(card)

                board = self.board + self.deck.draw(5 - len(self.board))
                # 计算牌力
                strength1 = self.evaluator.evaluate(self.hand, board)
                strength2 = self.evaluator.evaluate(opponent_hand, board)
                if strength1 < strength2:
                    wins += 1
            except:
                wins += random.randint(0, 1)
        return wins / num_simulations

    def print_class_name(self, strength):
        # 步骤 4: 获取牌型等级
        hand_class = self.evaluator.get_rank_class(strength)
        # 步骤 5: 获取牌型名称
        class_name = self.evaluator.class_to_string(hand_class)
        return strength, class_name


if __name__ == '__main__':
    hand1 = Hand('Ts', 'Kd')
    # hand.set_board('Ks', 'Kc', 'Qc', 'Qd')
    # rate = kk.win_rate(['Ts5c', 'AsAc'])
    # rate = kk.get_score()
    # hand1.add_board('4c')
    # hand1.add_board('Kc')
    # hand1.add_board('6d')
    # print(hand.eval())
    # hand.add_board('2d')
    # print(hand.eval())
    # hand.add_board('Ac')
    # print(hand1.get_strength())
    # cards1 = Cards('Ts', 'Qs', '7c', 'Kc', '4d', 'Jh', '2c')
    # val1 = cards1.lookup()
    # print(val1, cards1.to_string(val1))

    # kk = Cards(['Ks', 'Kd'])
    # rate = kk.win_rate(['AsKc'])
    # print(rate)
