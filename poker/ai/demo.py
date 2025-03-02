import torch
import torch.nn as nn
import torch.optim as optim
from treys import Evaluator, Card
import numpy as np
from collections import deque
import random


class PokerDRLAgent:
    def __init__(self):
        # 神经网络定义
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        # 强化学习参数
        self.gamma = 0.99
        self.memory = deque(maxlen=10000)
        self.batch_size = 64

        # 扑克专用工具
        self.evaluator = Evaluator()

    def _build_model(self):
        """定义深度Q网络结构"""
        return nn.Sequential(
            nn.Linear(18, 128),  # 输入层维度由特征工程决定
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 3)  # 输出层：fold/call/raise
        )

    def _feature_engineering(self, state):
        """特征工程：将扑克状态转换为神经网络输入"""
        # state包含：手牌/公共牌/底池/阶段/历史动作
        hand_strength = self._calculate_hand_potential(state['hand'], state['board'])
        pot_ratio = state['pot'] / (state['max_bet'] + 1e-5)
        phase_encoding = self._encode_phase(state['phase'])
        return np.concatenate([
            hand_strength,
            [pot_ratio],
            phase_encoding,
            state['action_history']
        ])

    def _calculate_hand_potential(self, hand, board):
        """使用treys计算牌力特征"""
        if len(board) == 0:
            return [0.0] * 5  # 预处理未发牌情况

        strength = self.evaluator.evaluate(hand, board)
        return [
            strength / 7462.0,  # 归一化牌力
            self.evaluator.get_rank_class(strength) / 10.0,
            self._outs_probability(hand, board),
            self._position_advantage(),
            self._stack_pot_ratio()
        ]

    def get_action(self, state, epsilon=0.1):
        """ε-greedy策略选择动作"""
        if np.random.rand() < epsilon:
            return np.random.choice(3)

        features = self._feature_engineering(state)
        q_values = self.model(torch.FloatTensor(features))
        return torch.argmax(q_values).item()

    def remember(self, state, action, reward, next_state, done):
        """存储经验到记忆库"""
        self.memory.append((
            self._feature_engineering(state),
            action,
            reward,
            self._feature_engineering(next_state),
            done
        ))

    def replay(self):
        """经验回放训练"""
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([x[0] for x in batch])
        actions = torch.LongTensor([x[1] for x in batch])
        rewards = torch.FloatTensor([x[2] for x in batch])
        next_states = torch.FloatTensor([x[3] for x in batch])
        dones = torch.FloatTensor([x[4] for x in batch])

        # DQN更新逻辑
        current_q = self.model(states).gather(1, actions.unsqueeze(1))
        next_q = self.target_model(next_states).max(1)[0].detach()
        target = rewards + (1 - dones) * self.gamma * next_q

        loss = nn.MSELoss()(current_q.squeeze(), target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_target_model(self):
        """更新目标网络"""
        self.target_model.load_state_dict(self.model.state_dict())

    def learn_from_result(self, episode_data):
        """从完整对局中学习"""
        # 实现蒙特卡洛回报分配
        returns = []
        R = 0
        for transition in reversed(episode_data):
            R = transition['reward'] + self.gamma * R
            returns.insert(0, R)

        # 优先经验回放
        for idx, ret in enumerate(returns):
            self.memory.append((
                self._feature_engineering(episode_data[idx]['state']),
                episode_data[idx]['action'],
                ret,
                self._feature_engineering(episode_data[idx]['next_state']),
                episode_data[idx]['done']
            ))

        # 自适应学习率调整
        if np.mean(returns) > 0:
            for param_group in self.optimizer.param_groups:
                param_group['lr'] *= 1.01
        else:
            for param_group in self.optimizer.param_groups:
                param_group['lr'] *= 0.99


# 初始化智能体
agent = PokerDRLAgent()