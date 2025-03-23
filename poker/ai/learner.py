import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from collections import deque
import random
from poker.ai.processor import StateProcessor


class PokerDrl(nn.Module):
    """深度强化学习核心网络"""

    def __init__(self, input_dim=18):
        super(PokerDrl, self).__init__()
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


class AdaptiveLearner:
    """自适应学习系统"""

    def __init__(self):
        # 策略网络（主网络）策略网络：实时更新的主网络，负责生成当前策略
        self.policy_net = PokerDrl()
        # 目标网络（延迟更新，稳定训练） 定期从策略网络同步参数，用于稳定Q值估算
        self.target_net = PokerDrl()
        # 同步目标网络参数. 双网络设计目的：解决强化学习中的"移动目标"问题 减少Q值过估计（Overestimation） 提高训练稳定性
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

