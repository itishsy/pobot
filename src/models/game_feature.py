from config.db import BaseModel
from peewee import IntegerField
from treys import Evaluator, Card, Deck
from .hand_score import HandScore
import json
import numpy as np
from itertools import combinations



def eval_strength(hand, board=None, opp_ranges=None, trials=5000, draw_size=2):
    """
    计算手牌强度
    """
    evaluator = Evaluator()
    community_cards = [] if board is None else [Card.new(v) if isinstance(v, str) else v for v in board]
    hand = [Card.new(v) if isinstance(v, str) else v for v in hand]
    used_cards = hand + community_cards
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
            opp_hand = deck.draw(draw_size)

        board = community_cards + deck.draw(5 - len(community_cards))

        # 计算牌力
        strength1 = evaluator.evaluate(hand, board)
        if len(opp_hand) == 2:
            strength2 = evaluator.evaluate(opp_hand, board)
        else:
            strength2 = 0
            hand_combs = list(combinations(opp_hand, 2))
            for han in hand_combs:
                strength2 = max(strength2, evaluator.evaluate([han[0], han[1]], board))

        if strength1 < strength2:
            wins += 1
        # except:
        #     print('error', hand)
        # wins += random.randint(0, 1)
    return round(wins / trials, 4)


def eval_wetness(community_cards):
    """
    评估公共牌湿润度，返回0-2的连续值（考虑成牌可能性和牌面强度）
    :param community_cards: 牌面列表，如 ['Ah', 'Kd', 'Qc', 'Js', 'Ts']
    :return:
    三张牌：['Ah', 'Kh', 'Qh'] 返回 1.23， ['2s', '7c', 'Qh'] 返回 0.03
    """

    def _card_value(card):
        """将牌面转换为数值（A=14，2=2）"""
        rank = card[:-1].upper()
        if rank == 'A': return 14
        if rank == 'K': return 13
        if rank == 'Q': return 12
        if rank == 'J': return 11
        if rank == 'T': return 10
        return int(rank)

    # 初始化数据结构
    cards = sorted([_card_value(c) for c in community_cards], reverse=True)
    suits = [c[-1].lower() for c in community_cards]
    result = {'straight': 0.0, 'flush': 0.0, 'pair': 0.0, 'high': 0.0}

    # ------------------ 顺子计算 ------------------
    unique_ranks = sorted(list(set(cards + [1 if r == 14 else r for r in cards])))  # 包含A作为1的情况
    straight_scores = []

    # 遍历所有可能的顺子组合
    for high in range(14, 4, -1):  # 从最大的A-high顺子开始检查
        target = set(range(high - 4, high + 1)) if high > 5 else {1, 2, 3, 4, 5}
        present = [r for r in unique_ranks if r in target]
        gap = 5 - len(present)

        if gap <= 2:  # 允许最多缺2张牌
            # 计算顺子强度：基础分 + 最大牌加成
            dif = max(present) - min(present)
            strength = (5 - gap) / 5 * 1.5 + (high / 14) * 0.5 - dif * 0.2
            straight_scores.append(min(strength, 2.0))
        elif len(community_cards) == 3 and gap == 3:
            dif = max(present) - min(present)
            strength = (5 - gap) / 5 * 1.5 + (high / 14) * 0.5 - dif * 0.2
            straight_scores.append(min(strength, 2.0))

    result['straight'] = max(straight_scores) if straight_scores else 0.0

    # ------------------ 同花计算 ------------------
    suit_counts = {}
    max_suit = None
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
        if suit_counts[s] > suit_counts.get(max_suit, 0):
            max_suit = s

    if max_suit and suit_counts[max_suit] >= 3:
        # 同花牌中的最大数值
        flush_cards = sorted([c for c, s in zip(cards, suits) if s == max_suit], reverse=True)
        # 计算同花强度：数量分（60%） + 最大牌分（40%）
        count_score = (suit_counts[max_suit] / 5) * 1.2  # 3张=0.72, 4张=0.96, 5张=1.2
        high_score = (flush_cards[0] / 14) * 0.8  # 最大牌占比
        result['flush'] = min(count_score + high_score, 2.0)
    elif max_suit and len(community_cards) == 3 and suit_counts[max_suit] == 2:
        # 同花牌中的最大数值
        flush_cards = sorted([c for c, s in zip(cards, suits) if s == max_suit], reverse=True)
        # 计算同花强度：数量分（60%） + 最大牌分（40%）
        count_score = (suit_counts[max_suit] / 5) * 0.6  # 3张=0.72, 4张=0.96, 5张=1.2
        high_score = (flush_cards[0] / 14) * 0.4  # 最大牌占比
        result['flush'] = min(count_score + high_score, 2.0)

    # ------------------ 对子计算 ------------------
    rank_counts = {}
    for r in cards:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    # 计算对子强度（考虑对子大小和数量）
    pairs = sorted([r for r, cnt in rank_counts.items() if cnt >= 2], reverse=True)
    set_score = 0.0
    if len(pairs) >= 2:  # 两对
        set_score = (pairs[0] + pairs[1]) / 28 * 1.9  # AA+KK=27/28*1.5≈1.45
    elif len(pairs) == 1:  # 一对
        set_score = pairs[0] / 14 * 0.9  # AA=14/14*1=1.0

    # 三条/葫芦额外加分
    trips = [r for r, cnt in rank_counts.items() if cnt >= 3]
    if trips:
        set_score += (sum(trips) / 14) * 0.5  # 三条加成

    result['pair'] = min(set_score, 2.0)

    # ------------------ 高张计算 ------------------
    high_cards = [r for r in cards if r >= 11]  # J以上算高牌
    unique_high = sorted(list(set(high_cards)), reverse=True)

    # 强度计算规则：
    # - 每张高牌基础分：A=0.5, K=0.4, Q=0.3, J=0.2
    # - 组合加成：同时有AK加0.5，AQ加0.3等
    base_scores = {14: 0.5, 13: 0.4, 12: 0.3, 11: 0.2}
    score = sum(base_scores.get(r, 0) for r in unique_high)

    # 组合加成
    if 14 in unique_high and 13 in unique_high: score += 0.5  # AK
    if 14 in unique_high and 12 in unique_high: score += 0.3  # AQ
    if 13 in unique_high and 12 in unique_high: score += 0.2  # KQ

    result['high'] = min(score * 1.5, 2.0)  # 最高得分2.0

    return {k: round(v, 1) for k, v in result.items()}
    # 四舍五入保留1位小数
    # return wetness_level({k: round(v, 1) for k, v in result.items()}, len(community_cards))



class GameFeature(BaseModel):
    """
    特征值。反映客观存在的数据
    """
    class Meta:
        table_name = 'game_feature'

    stage = IntegerField()          # 1. 階段。0（preflop）、1（flop）、2（turn）、3（river）
    pos = IntegerField()            # 2. 位置。0（先手）、1（中间）、2（后手）
    pots = IntegerField()           # 3. 底池大小。換算成BB的底池大小（BB）
    ppots = IntegerField()          # 4. 翻牌前底池大小（BB）
    calls = IntegerField()          # 5. 跟注大小（BB）
    players = IntegerField()        # 6. 玩家数。本階段仍活跌的入池玩家人數
    c_bet = IntegerField()          # 7. 持续下注玩家。0（无）、1（一個）、2（两個及以上）
    c_bet_his = IntegerField()      # 8. 持续下注次数（本局比賽中）
    c_raise = IntegerField()        # 9. 过牌加注。0（无）、1（一個）、2（两個及以上）
    c_raise_his = IntegerField()    # 10. 过牌加注次数（本局比賽中）
    b_bet = IntegerField()          # 11. 大额下注。0（无）、1（一個）、2（两個及以上）
    b_bet_his = IntegerField()      # 12. 大额下注次数
    strength = IntegerField()       # 13. 手牌强度，取值范围0-100
    wet_high = IntegerField()       # 14. 公共牌高张。0（无）、1（一张）、2（两张及以上）
    wet_pair = IntegerField()       # 15. 公共牌对子。0（无）、1（一对）、2（两对或三条）
    wet_straight = IntegerField()   # 16. 公共牌顺子。0（无）、1（两张成顺）、2（单张成顺）
    wet_flush = IntegerField()      # 17. 公共牌同色。0 (无)、1（两张成花）、2（单张成花）

    # def __init__(self):
    #     self.stage = None           # 0（preflop）、1（flop）、2（turn）、3（river）
    #     self.pos = None             # 0（先手）、1（中间）、2（后手）
    #     self.pots = None            # 底池大小（BB）
    #     self.calls = None           # 跟注大小（BB）
    #     self.ppots = None           # 翻牌前底池大小（BB）
    #     self.players = None         # 玩家数
    #     self.c_bet = None           # 当前阶段存在持续下注。0（无）、1（一个玩家）、2（两个及以上玩家）
    #     self.c_bet_his = None       # 持续下注次数
    #     self.c_raise = None         # 当前阶段存在过牌加注。0（无）、1（一个玩家）、2（两个及以上玩家）
    #     self.c_raise_his = None     # 过牌加注次数
    #     self.b_bet = None           # 当前阶段存在大额下注。0（无）、1（一个玩家）、2（两个及以上玩家）
    #     self.b_bet_his = None       # 大额下注次数
    #     self.strength = None        # 手牌强度，取值范围0-1
    #     self.wet_high = 0           # 公共牌高张。0（无）、1（一张）、2（两张及以上）
    #     self.wet_pair = 0           # 公共牌对子。0（无）、1（一对）、2（两对或三条）
    #     self.wet_straight = 0       # 公共牌顺子。0（无）、1（两张成顺）、2（单张成顺）
    #     self.wet_flush = 0          # 公共牌同色。0 (无)、1（两张成花）、2（单张成花）
    #     self.wet = None             # 牌面湿润度，取值范围0-2

    # def process(self, game):
    #     state = game.states[-1]
    #     self.stage = state.stage
    #     self.pos = self._pos(state)
    #     self.pots = round(state.pot/game.bb, 2)
    #     self.calls = round(state.call/game.bb, 2)
    #     self.ppots = round([s for s in game.states if s.stage == 0][-1].pot/game.bb, 2)
    #     self.players = len(state.actives())
    #     self.c_bet = self._c_bet(game.states)
    #     self.c_raise = self._check_raise(game.states)
    #     self.b_bet = self._big_bet()
    #     self.strength = self._strength(state.hand, state.board)
    #     wetness = self._wetness(state.board)
    #     self.wet_high = wetness['high']
    #     self.wet_pair = wetness['pair']
    #     self.wet_straight = wetness['straight']
    #     self.wet_flush = wetness['flush']
    #     self.wet = wetness['wetness']

    @staticmethod
    def process(game):
        feature = GameFeature()
        state = game.states[-1]
        feature.stage = state.stage
        feature.pos = feature._pos(state)
        feature.pots = round(state.pot / game.bb, 2)
        feature.calls = 0 if state.call is None else round(state.call / game.bb, 2)
        feature.ppots = round([s for s in game.states if s.stage == 0][-1].pot / game.bb, 2)
        feature.players = len(state.actives())
        feature.c_bet = feature._c_bet(game.states)
        feature.c_raise = feature._check_raise(game.states)
        feature.b_bet = feature._big_bet()
        feature.strength = feature._strength(state.hand, state.board)
        wetness = feature._wetness(state.board)
        feature.wet_high = wetness['high']
        feature.wet_pair = wetness['pair']
        feature.wet_straight = wetness['straight']
        feature.wet_flush = wetness['flush']
        return feature

    def to_dict(self):
        return {
            'stage': self.stage,
            'pos': self.pos,
            'pots': self.pots,
            'calls': self.calls,
            'ppots': self.ppots,
            'players': self.players,
            'c_bet': self.c_bet,
            'c_raise': self.c_raise,
            'b_bet': self.b_bet,
            'strength': self.strength,
            'wet_high': self.wet_high,
            'wet_pair': self.wet_pair,
            'wet_straight': self.wet_straight,
            'wet_flush': self.wet_flush
        }

    @staticmethod
    def _pos(state):
        """
        位置
        """
        cur_players = state.pls
        min_pos, max_pos = 1, 6
        for p in cur_players:
            min_pos = min(min_pos, p.position)
            max_pos = max(max_pos, p.position)
        if state.position < min_pos:
            return 0
        if state.position > max_pos:
            return 2
        return 1

    @staticmethod
    def _c_bet(states):
        """
        持续下注，当前两个state均下注
        """
        c_bet = 0
        cur_state = states[-1]
        pre_state = states[-2]
        for i in range(5):
            cur_player = cur_state.pls[i]
            if cur_player.active and cur_player.action in ['bet', 'raise'] and pre_state.pls[i].action in ['bet', 'raise']:
                c_bet = c_bet + 1
        return c_bet

    @staticmethod
    def _check_raise(states):
        """
        过牌加注
        """
        c_raise = 0
        cur_state = states[-1]
        pre_state = states[-2]
        if cur_state.stage == pre_state.stage:
            for i in range(5):
                cur_player = cur_state.pls[i]
                if cur_player.active and cur_player.action == 'raise' and pre_state.pls[i].action == 'check':
                    c_raise = c_raise + 1
        return c_raise

    def _big_bet(self):
        """
        大额下注
        """
        b_bet = 0
        if self.stage == 0:
            if 25 > self.calls > 10:
                b_bet = 1
            if self.calls >= 25:
                b_bet = 2
        else:
            pot = self.pots - self.calls
            if self.calls > max(pot * 0.5, 10):
                b_bet = 1
            if self.calls > max(pot * 0.8, 25):
                b_bet = 2
        return b_bet

    def _strength(self, hand, board):
        """
        牌面强度。 不考虑玩家的范围及行为
        """
        # if self.stage == 0:
        #     strength = HandScore.get_score(hand[0], hand[1])
        # else:
        strength = eval_strength(hand, board, trials=10000, draw_size=3)
        return round(strength, 2)

    @staticmethod
    def _wetness(board):
        """
        # 湿润程度 0 干燥  1 湿润  2 非常湿润
        """
        result = eval_wetness(board)
        size = len(board)
        straight = result['straight']
        flush = result['flush']
        pair = result['pair']
        high = result['high']
        wetness = 0
        if size == 3:
            if high > 1.3 or pair > 0.7 or flush > 1 or straight > 1:
                # 三同花、三连牌、大公对、两高张、三张
                wetness = 2
            elif high > 0.5 or pair > 0 or flush > 0.5 or straight > 0.5:
                # 两同花、两连牌、小公对、高张、
                wetness = 1
        elif size == 4:
            if high > 1.3 or pair > 0.7 or flush > 1 or straight > 1:
                # 三同花、三连牌、大公对、两高张、三张
                wetness = 2
            elif high > 0.5 or pair > 0 or flush > 0.5 or straight > 0.5:
                # 两同花、两连牌、小公对、高张、
                wetness = 1
        else:
            if high > 1.3 or pair > 0.7 or flush > 1 or straight > 1:
                # 三同花、三连牌、大公对、两高张、三张
                wetness = 2
            elif high > 0.5 or pair > 0 or flush > 0.5 or straight > 0.5:
                # 两同花、两连牌、小公对、高张、
                wetness = 1
        result['wetness'] = wetness
        return result
