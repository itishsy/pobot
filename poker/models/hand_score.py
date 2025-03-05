from treys import Evaluator, Card, Deck
from models.base import BaseModel, db
from flask_peewee.db import CharField, FloatField, DateTimeField, AutoField, FloatField
from datetime import datetime
from itertools import combinations


class HandScore(BaseModel):
    id = AutoField()
    hand = CharField()
    score = FloatField()


def eval_score(hand, num_simulations = 10000):
    for _ in range(num_simulations):
        try:
            # 创建新的牌堆
            deck = Deck()

            deck.cards.remove(hand[0])
            deck.cards.remove(hand[1])

            # 底牌范围中随机抽取一手牌
            opponent_hand = opponent_hand = deck.draw(2)

            # 从牌堆中移除已出现的牌
            used_cards = hand + opponent_hand
            for card in used_cards:
                if card in deck.cards:
                    deck.cards.remove(card)
            
            board = []
            board += deck.draw(5 - len(board))

            # 计算牌力
            strength1 = self.evaluator.evaluate(self.hand, board)
            strength2 = self.evaluator.evaluate(opponent_hand, board)
            if strength1 < strength2:
                wins += 1
        except:
            wins += random.randint(0, 1)
    return wins / num_simulations


def main():
    # 定义所有牌面
    suits = ['s', 'h', 'd', 'c']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

    # 生成所有可能的单张牌
    all_cards = [Card.new(rank + suit) for rank in ranks for suit in suits]

    # 生成所有可能的两张手牌组合
    all_hand_combinations = combinations(all_cards, 2)

    # 遍历所有手牌组合并计算得分
    for hand in all_hand_combinations:
        # 避免手牌和公共牌重复
        if not any(card in hand for card in board):
            score = simulate()
            hand_str = ' '.join([Card.int_to_str(card) for card in hand])
            print(f"手牌: {hand_str}, 强度得分: {score}")


if __name__ == '__main__':
    hs = HandScore()
    hand1 = ['As', 'Kc']
    score1 = eval_score(hand)
    print(f"hand: {hand1}, score: {score1}")
    