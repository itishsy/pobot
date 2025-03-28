from treys import Evaluator, Card, Deck
from models.base import BaseModel, db
from flask_peewee.db import CharField, AutoField, FloatField
from itertools import combinations
import random
import numpy as np
from poker.config import BB
from collections import defaultdict
from enum import Enum


class HandScore(BaseModel):
    class Meta:
        table_name = 'hand_score'

    id = AutoField()
    hand = CharField()
    score = FloatField()

    @staticmethod
    def get_score(card1, card2):
        hs = HandScore.select().where((HandScore.hand == (card1 + card2)) | (HandScore.hand == (card2 + card1))).first()
        return hs.score

    @staticmethod
    def get_ranges(min_score, max_score):
        ranges = []
        lis = HandScore.select().where((HandScore.score >= min_score) & (HandScore.score <= max_score))
        for hs in lis:
            ranges.append(hs.hand)
        return ranges

class BoardType(Enum):
    straight_flush_five = 1001
    straight_flush_four = 1002 
    straight_flush_three = 1003
    flush_four = 2001       # 四张同色
    flush_three = 2002       # 三张同色
    straight_middle = 3001    # 卡顺
    straight_both = 3002    # 两头顺
    two_pair = 4001    # 两公对
    pair = 5001    # 一公对
    high = 9001    # 高张
    

def eval_strength(hand, board=None, opp_ranges=None, trials=5000):
    evaluator = Evaluator()
    self_board = [] if board is None else [Card.new(v) if isinstance(v, str) else v for v in board]
    hand = [Card.new(v) if isinstance(v, str) else v for v in hand]
    used_cards = hand + self_board
    opp_ranges = [[Card.new(v[0:2]), Card.new(v[2:4])] for v in opp_ranges] if opp_ranges is not None else []
    opp_hands = []
    for r in opp_ranges:
        if r[0] not in used_cards and r[1] not in used_cards:
            opp_hands.append(r)
    deck = Deck()

    wins = 0
    for _ in range(trials):
        # try:
        deck.shuffle()

        for card in used_cards:
            deck.cards.remove(card)

        # 底牌范围中随机抽取一手牌
        if len(opp_hands) > 0:
            opp_hand = opp_hands[np.random.randint(0, len(opp_hands))]
            deck.cards.remove(opp_hand[0])
            deck.cards.remove(opp_hand[1])
        else:
            opp_hand = deck.draw(2)

        board = self_board + deck.draw(5 - len(self_board))

        # 计算牌力
        strength1 = evaluator.evaluate(hand, board)
        strength2 = evaluator.evaluate(opp_hand, board)
        if strength1 < strength2:
            wins += 1
        # except:
        #     print('error', hand)
        # wins += random.randint(0, 1)
    return wins / trials


def basic_strength(hand, board):
    evaluator = Evaluator()
    self_board = [] if board is None else [Card.new(v) if isinstance(v, str) else v for v in board]
    hand = [Card.new(v) if isinstance(v, str) else v for v in hand]
    if len(self_board) > 0:
        strength = evaluator.evaluate(hand, self_board)
        return round((1 - strength / 7462),4)
    else:
        hand_str = ''.join([Card.int_to_str(card) for card in hand])
        hs = HandScore.select().where(HandScore.hand == hand_str).first()
        return hs


def wet_board(board):
    """评估牌面湿润程度（0-1范围）"""

    self_board = [] if board is None else [Card.new(v) if isinstance(v, str) else v for v in board]

    # 湿润度影响因素
    wetness = 0.0
    suits = defaultdict(int)
    ranks = []

    # 统计花色和点数
    for card in self_board:
        suits[Card.get_suit_int(card)] += 1
        ranks.append(Card.get_rank_int(card))

    # 同花潜力
    max_suit = max(suits.values(), default=0)
    if max_suit >= 2:
        wetness += 0.3 * (max_suit / 3)

    # 顺子潜力
    sorted_ranks = sorted(set(ranks))
    gaps = 0
    for i in range(1, len(sorted_ranks)):
        gaps += sorted_ranks[i] - sorted_ranks[i - 1] - 1
    if gaps <= 2:
        wetness += 0.4 * (1 - gaps / 3)

    # 对子/三条潜力
    rank_counts = defaultdict(int)
    for r in ranks:
        rank_counts[r] += 1
    if any(c >= 2 for c in rank_counts.values()):
        wetness += 0.3

    return min(wetness, 1.0)  # 限制在0-1范围


def refresh_hand_score():
    # 定义所有牌面
    suits = ['s', 'h', 'd', 'c']
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

    # 生成所有可能的单张牌
    all_cards = [Card.new(rank + suit) for rank in ranks for suit in suits]

    # 生成所有可能的两张手牌组合
    all_hand_combinations = combinations(all_cards, 2)

    # 遍历所有手牌组合并计算得分
    for hand in all_hand_combinations:
        # 避免手牌和公共牌重复
        score = eval_strength([hand[0], hand[1]])
        hand_str = ''.join([Card.int_to_str(card) for card in hand])
        hs = HandScore.select().where(HandScore.hand == hand_str).first()
        hs.score = round((score + hs.score)/2, 4)
        hs.save()
        print(f"hand: {hand_str}, score: {score}, update: {hs.score}")


if __name__ == '__main__':
    refresh_hand_score()
    # db.connect()
    # db.create_tables([HandScore])
    # hand1 = [Card.new('As'),  Card.new('Kc')]
    # score1 = eval_score(hand1)
    # hand_str1 = ''.join([Card.int_to_str(card) for card in hand1])
    # hs1 = HandScore()
    # hs1.hand = hand_str1
    # hs1.score = score1
    # print(f"hand: {hand_str1}, score: {score1}")
    # hs1.save()
