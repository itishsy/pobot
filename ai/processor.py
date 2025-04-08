from treys import Evaluator, Card, Deck
from collections import deque, defaultdict
import random
import numpy as np


class StateProcessor:
    """牌局状态处理器"""

    def __init__(self):
        self.evaluator = Evaluator()
        self.position_encoder = {
            'BTN': [1, 0, 0, 0], 'SB': [0, 1, 0, 0],
            'BB': [0, 0, 1, 0], 'UTG': [0, 0, 0, 1]
        }
        self.opponent_history = defaultdict(lambda: {
            'vpip': 0.5,  # 初始假设玩家入池率50%
            'pfr': 0.2,  # 初始假设翻牌前加注率20%
            'aggression': 0.3,  # 初始激进指数
            'cbet': 0.0,  # 持续下注率
            'showdown': 0.0  # 摊牌倾向
        })

    def process(self, state):
        """将原始状态转换为特征向量"""
        # 手牌强度特征
        hand_strength = self._calc_hand_strength(state['hand'], state['board'])

        # 位置特征
        pos_feat = self.position_encoder[state['position']]

        # 资金动态特征
        stack_ratio = state['my_stack'] / sum(p['stack'] for p in state['players'])

        # 对手行为特征
        opp_features = self._encode_opponents(state['players'])

        # 公共牌阶段
        phase_feat = [0] * 4
        phase_feat[len(state['board']) // 3] = 1

        return np.concatenate([
            hand_strength,
            pos_feat,
            [stack_ratio],
            opp_features,
            phase_feat,
            [state['pot'] / 1000]  # 归一化底池
        ])

    def _calc_hand_strength(self, hand, board):
        """计算手牌潜力特征"""
        if len(board) == 0:
            return [0.0] * 3
        strength = self.evaluator.evaluate(hand, board)
        return [
            strength / 7462.0,
            self.evaluator.get_rank_class(strength) / 10.0,
            self._estimate_equity(hand, board)
        ]

    def _estimate_equity(self, hand, board, trials=500):
        """蒙特卡洛胜率估算"""
        deck = Deck()
        remaining = [c for c in deck.cards if c not in hand + board]
        wins = 0

        for _ in range(trials):
            opp_hand = random.sample(remaining, 2)
            community = board + random.sample([c for c in remaining if c not in opp_hand], 5 - len(board))

            our_strength = self.evaluator.evaluate(hand, community)
            opp_strength = self.evaluator.evaluate(opp_hand, community)
            wins += 1 if our_strength < opp_strength else 0

        return wins / trials

    def _encode_opponents(self, players):
        """
        编码对手行为特征（返回9维向量）
        特征设计：
        [
            对手1_vpip, 对手1_pfr, 对手1_aggression,
            对手2_vpip, 对手2_pfr, 对手2_aggression,
            平均cbet率, 平均摊牌率, 位置威胁系数
        ]
        """
        features = []
        cbet_total = 0
        showdown_total = 0
        position_threat = 0

        for idx, player in enumerate(players):
            # 获取玩家历史数据
            player_id = player['id']
            hist = self.opponent_history[player_id]

            # 更新动态参数（带衰减因子）
            self._update_player_stats(player, hist)

            # 添加个体特征
            features.extend([
                hist['vpip'],  # 入池率 (0-1)
                hist['pfr'],  # 翻牌前加注率 (0-1)
                hist['aggression']  # 激进指数 (0-1)
            ])

            # 收集全局统计
            cbet_total += hist['cbet']
            showdown_total += hist['showdown']

            # 计算位置威胁（根据位置和筹码量）
            position_weight = {
                'BTN': 0.5, 'SB': 0.3,
                'BB': 0.2, 'UTG': 0.4
            }.get(player['position'], 0.1)
            stack_ratio = player['stack'] / (self.my_stack + 1e-5)
            position_threat += position_weight * stack_ratio

        # 添加全局特征
        num_opponents = len(players)
        features.append(cbet_total / num_opponents)  # 平均持续下注率
        features.append(showdown_total / num_opponents)  # 平均摊牌率
        features.append(position_threat)  # 综合位置威胁

        return np.array(features, dtype=np.float32)

    def _update_player_stats(self, player, hist):
        """
        动态更新对手统计数据（带指数衰减）
        参数：
            player: 当前玩家对象（包含最新动作）
            hist: 该玩家的历史统计记录
        """
        alpha = 0.2  # 学习率，控制新数据的权重

        # VPIP（入池率）更新
        if player['acted_this_round']:
            new_vpip = 1 if player['action'] != 'fold' else 0
            hist['vpip'] = (1 - alpha) * hist['vpip'] + alpha * new_vpip

        # PFR（翻牌前加注率）更新
        if player['stage'] == 'preflop':
            new_pfr = 1 if 'raise' in player['actions'] else 0
            hist['pfr'] = (1 - alpha) * hist['pfr'] + alpha * new_pfr

        # 激进指数计算（加注次数占比）
        total_actions = len(player['actions'])
        raise_count = sum(1 for a in player['actions'] if a == 'raise')
        hist['aggression'] = raise_count / (total_actions + 1e-5)

        # CBet率更新（翻牌后作为进攻方首次下注）
        if player['stage'] == 'flop' and player['is_aggressor']:
            new_cbet = 1 if 'bet' in player['actions'] else 0
            hist['cbet'] = (1 - alpha) * hist['cbet'] + alpha * new_cbet

        # 摊牌率更新（进入摊牌并亮牌的概率）
        if player['showdown']:
            hist['showdown'] = (1 - alpha) * hist['showdown'] + alpha * 1
