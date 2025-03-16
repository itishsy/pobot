from treys import Evaluator, Card, Deck
from models.base import BaseModel, db
from flask_peewee.db import CharField, AutoField, FloatField
from itertools import combinations
import random
import numpy as np
from poker.config import BB


class HandScore(BaseModel):
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


def eval_score(hand, num_simulations=10000):
    wins = 0
    evaluator = Evaluator()
    for _ in range(num_simulations):
        try:
            # 创建新的牌堆
            deck = Deck()

            deck.cards.remove(hand[0])
            deck.cards.remove(hand[1])

            # 底牌范围中随机抽取一手牌
            opponent_hand = deck.draw(2)

            # 从牌堆中移除已出现的牌
            used_cards = hand + opponent_hand
            for card in used_cards:
                if card in deck.cards:
                    deck.cards.remove(card)
            
            board = []
            board += deck.draw(5 - len(board))

            # 计算牌力
            strength1 = evaluator.evaluate(hand, board)
            strength2 = evaluator.evaluate(opponent_hand, board)
            if strength1 < strength2:
                wins += 1
        except:
            wins += random.randint(0, 1)
    return wins / num_simulations


def main():
    # 定义所有牌面
    suits = ['s', 'h', 'd', 'c']
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

    # 生成所有可能的单张牌
    all_cards = [Card.new(rank + suit) for rank in ranks for suit in suits]

    # 生成所有可能的两张手牌组合
    all_hand_combinations = combinations(all_cards, 2)

    # 遍历所有手牌组合并计算得分
    for hand in all_hand_combinations:
        hs = HandScore()
        # 避免手牌和公共牌重复
        score = eval_score([hand[0], hand[1]])
        hand_str = ''.join([Card.int_to_str(card) for card in hand])
        hs.hand = hand_str
        hs.score = score
        hs.save()
        print(f"hand: {hand_str}, score: {score}")


if __name__ == '__main__':
    pass
    # main()
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
