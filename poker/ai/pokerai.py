import torch
import torch.nn as nn
import torch.optim as optim
from treys import Evaluator, Card, Deck
import numpy as np
from collections import deque, defaultdict
import random


class PokerAI(nn.Module):
    """深度强化学习核心网络"""

    def __init__(self, input_dim=18):
        super(PokerAI, self).__init__()
        # 特征提取层：将原始输入转换为高级特征表示
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, 256),  # 全连接层，输入维度18，输出256
            nn.LayerNorm(256),  # 层归一化，稳定训练过程
            nn.ELU()  # 激活函数，相比ReLU更平滑
        )
        # 动作头：输出各动作的概率分布
        self.action_head = nn.Sequential(
            nn.Linear(256, 128),  # 全连接层
            nn.ELU(),  # 激活函数
            nn.Linear(128, 3)  # 输出3个动作的概率：fold/call/raise
        )
        # 价值头：评估当前状态的期望收益
        self.value_head = nn.Sequential(
            nn.Linear(256, 128),  # 全连接层
            nn.ELU(),
            nn.Linear(128, 1)  # 输出单个标量值表示状态价值
        )

    def forward(self, x):
        """
        前向传播过程
        参数：
            x: 输入状态张量，形状(batch_size, input_dim)
        返回：
            action_probs: 动作概率分布，形状(batch_size, 3)
            state_value: 状态价值估计，形状(batch_size, 1)
        """
        # 特征提取
        features = self.feature_extractor(x)  # 输出形状(batch_size, 256)
        # 计算动作概率分布（使用softmax归一化）
        action_probs = torch.softmax(self.action_head(features), dim=-1)  # 转换为概率
        # 计算状态价值
        state_value = self.value_head(features)  # 形状(batch_size, 1)
        return action_probs, state_value


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
        phase_feat[len(state['board'] // 3] = 1

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

class AdaptiveLearner:
    """自适应学习系统"""

    def __init__(self):
        # 策略网络（主网络）
        self.policy_net = PokerAI()
        # 目标网络（延迟更新，稳定训练）
        self.target_net = PokerAI()
        # 同步目标网络参数
        self.target_net.load_state_dict(self.policy_net.state_dict())

        # 优化器：AdamW（带权重衰减的Adam）
        self.optimizer = optim.AdamW(
            self.policy_net.parameters(),
            lr=3e-4,  # 学习率
            weight_decay=1e-5  # L2正则化项
        )

        # 经验回放缓冲区（最大存储1万条经验）
        self.memory = deque(maxlen=10000)
        # 折扣因子（未来奖励的衰减率）
        self.gamma = 0.99
        # 批次大小（每次更新采样128条经验）
        self.batch_size = 128

        # 状态处理器（将原始数据转换为特征向量）
        self.state_processor = StateProcessor()
        # 损失函数（Huber损失，对异常值鲁棒）
        self.loss_fn = nn.SmoothL1Loss()

    def get_action(self, state, exploration=0.1):
        """获取决策动作。根据当前状态选择动作
        参数：
            state: 原始状态字典
            exploration: 探索率（随机动作的概率）
        返回：
            action: 动作索引（0:fold, 1:call, 2:raise）
            predicted_value: 当前状态的价值预测
        """
        # 不计算梯度（推理阶段）
        with torch.no_grad():
            # 将状态转换为特征张量
            state_tensor = torch.FloatTensor(
                self.state_processor.process(state)
            )  # 形状(1, input_dim)

            # 获取网络输出
            probs, value = self.policy_net(state_tensor)

            # ε-greedy策略：以exploration概率随机选择动作
            if random.random() < exploration:
                return random.choice(range(3)), value.item()
            # 选择概率最高的动作
            return torch.argmax(probs).item(), value.item()

    def update_model(self):
        """使用经验回放更新模型"""
        # 经验不足时不更新
        if len(self.memory) < self.batch_size:
            return

        # 从缓冲区随机采样一个批次
        batch = random.sample(self.memory, self.batch_size)
        # 解包经验元组
        states, actions, rewards, next_states, dones = zip(*batch)

        # 转换为PyTorch张量
        state_tensors = torch.stack([torch.FloatTensor(s) for s in states])
        next_state_tensors = torch.stack(
            [torch.FloatTensor(s) if s is not None else torch.zeros_like(state_tensors[0])
             for s in next_states]
        )
        action_tensors = torch.LongTensor(actions)
        reward_tensors = torch.FloatTensor(rewards)
        done_tensors = torch.BoolTensor(dones)

        # --- 计算目标Q值 ---
        with torch.no_grad():  # 目标网络不计算梯度
            _, next_values = self.target_net(next_state_tensors)
            # 目标值 = 即时奖励 + γ * 下一状态价值（未结束时）
            target_values = reward_tensors + (~done_tensors) * self.gamma * next_values.squeeze()


        # 计算当前Q值
        # 前向传播获取动作概率和状态价值
        action_probs, current_values = self.policy_net(state_tensors)
        # 提取所选动作的概率
        selected_action_probs = action_probs.gather(1, action_tensors.unsqueeze(1))

        # --- 计算损失 ---
        # 策略梯度损失（带基线）
        policy_loss = -torch.log(selected_action_probs) * (target_values - current_values.squeeze()).detach()
        policy_loss = policy_loss.mean()

        # 价值函数损失（预测值与目标值的差距）
        value_loss = self.loss_fn(current_values.squeeze(), target_values)

        # 总损失（加权求和）
        total_loss = policy_loss + 0.5 * value_loss

        # --- 反向传播 ---
        self.optimizer.zero_grad()  # 清空梯度
        total_loss.backward()  # 计算梯度
        # 梯度裁剪（防止梯度爆炸）
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()  # 更新参数

    def learn_from_episode(self, episode):
        """从完整牌局中学习（蒙特卡洛方法）"""
        # 计算累计回报（从最后一步向前计算）
        returns = []
        r = 0  # 最终回报
        for t in reversed(range(len(episode))):
            r = episode[t]['reward'] + self.gamma * r
            returns.insert(0, r)

        # 存储经验到缓冲区
        for t in range(len(episode)):
            state = self.state_processor.process(episode[t]['state'])
            next_state = self.state_processor.process(episode[t + 1]['state']) if t + 1 < len(episode) else None
            # 添加到经验池
            self.memory.append((
                state,
                episode[t]['action'],
                returns[t],
                next_state if next_state is not None else np.zeros_like(state),
                t == len(episode) - 1
            ))

        # 软更新目标网络（逐步同步参数）
        target_net_state = self.target_net.state_dict()
        policy_net_state = self.policy_net.state_dict()
        # 使用混合系数tau=0.01进行加权平均
        for key in policy_net_state:
            target_net_state[key] = policy_net_state[key] * 0.01 + target_net_state[key] * 0.99

        # 执行多次参数更新（提高数据利用率）
        for _ in range(2):
            self.update_model()


class BankrollManager:
    """资金管理系统（基于改进凯利公式）"""

    def __init__(self, initial=1000):
        self.bankroll = initial  # 初始资金
        self.kelly_factor = 0.1  # 凯利系数
        self.bet_history = []  # 下注历史记录

    def get_bet_size(self, action_prob, pot_size):
        """
        计算最优下注量
        参数：
            action_prob: 模型输出的动作概率（[fold_prob, call_prob, raise_prob]）
            pot_size: 当前底池大小
        返回：
            建议下注量
        """
        win_prob = action_prob[2]  # 取raise动作的概率作为赢率估计
        edge = win_prob - (1 - win_prob)  # 计算优势 edge = p_win - p_lose

        if edge <= 0:
            return 0  # 没有优势时不加注

        # 凯利公式：f = (bp - q)/b
        # 这里简化为 f = edge / (pot_odds)
        pot_odds = pot_size / self.bankroll
        fraction = edge / pot_odds

        # 应用风险系数
        bet = self.bankroll * self.kelly_factor * fraction
        # 限制最大下注量（不超过底池的50%）
        return min(bet, pot_size * 0.5)

    def update(self, result):
        """更新资金状态"""
        self.bankroll += result
        self.bet_history.append(result)

        # 动态调整风险系数（根据资金量变化）
        if self.bankroll < 500:  # 资金不足时保守
            self.kelly_factor = 0.05
        elif self.bankroll > 2000:  # 资金充足时激进
            self.kelly_factor = 0.15
        else:  # 正常状态
            self.kelly_factor = 0.1

