import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd
import joblib
import os
from typing import Tuple, List, Dict, Optional, Union


"""

核心设计思想
该系统本质是深度 Q 网络（DQN） 的简化实现：
输入是 "状态特征 + 动作" 的组合，输出是该组合对应的预期奖励（Q 值）；
训练时通过历史数据中的真实奖励优化 Q 值预测；
推理时通过比较所有动作的 Q 值选择最优解。
适用于需要基于历史 "状态 - 动作 - 反馈" 数据学习决策的场景（不仅限于扑克，也可扩展到其他离散动作的决策问题）。

"""


# =====================
# 数据预处理与特征工程
# =====================
class PokerDataProcessor:
    """
    负责将原始数据转换为模型可输入的格式，核心是处理特征标准化和动作编码，为模型学习做准备。

    核心功能：
    1. 数据校验：检查输入数据是否包含必要的action（动作）和reward（奖励）列。
    2. 特征处理：    自动推断特征列（排除action和reward）；    使用StandardScaler对特征进行标准化（均值为 0、方差为 1），避免不同尺度特征对模型的影响。
    3. 动作编码：    动态获取数据中所有 unique 动作，构建action_mapping（原始动作→索引）；    将动作转换为 one-hot 编码（如动作 0→[1,0,0]，动作 1→[0,1,0]），便于模型理解离散动作。
    4. 输入拼接：将标准化后的特征与 one-hot 动作编码拼接，作为模型的输入（因为模型需要同时基于 "当前状态特征" 和 "采取的动作" 预测奖励）。
    5. 持久化：通过save/load方法保存 / 加载预处理参数（标准化器、特征列、动作映射），确保训练和推理时的预处理逻辑一致。
    """

    def __init__(self, feature_columns: Optional[List[str]] = None):
        self.feature_columns = feature_columns
        self.action_col = 'action'
        self.reward_col = 'reward'
        self.scaler = StandardScaler()  # 仅保留特征标准化器
        self.action_dim: Optional[int] = None  # 动态确定动作维度
        self.action_mapping: Optional[Dict[int, int]] = None  # 动作到索引的映射

    def process(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """处理原始数据框，返回特征矩阵和奖励数组"""
        # 检查必要列是否存在
        required_cols = [self.action_col, self.reward_col]
        if not set(required_cols).issubset(df.columns):
            missing = set(required_cols) - set(df.columns)
            raise ValueError(f"数据缺少必要列：{missing}")

        # 推断特征列
        if self.feature_columns is None:
            self.feature_columns = [col for col in df.columns
                                   if col not in [self.action_col, self.reward_col]]
        
        # 提取并标准化特征
        features = df[self.feature_columns].values.astype(np.float32)
        features = self.scaler.fit_transform(features)
        num_features = features.shape[1]
        print(f'特征数: {num_features}, 样本数: {features.shape[0]}')

        # 动态处理动作编码
        actions = df[self.action_col].values
        unique_actions = np.unique(actions)
        self.action_dim = len(unique_actions)
        self.action_mapping = {a: i for i, a in enumerate(unique_actions)}
        
        # 生成one-hot编码
        action_encoded = np.zeros((len(actions), self.action_dim), dtype=np.float32)
        for i, action in enumerate(actions):
            action_encoded[i, self.action_mapping[action]] = 1.0

        # 拼接特征与动作编码
        processed = np.hstack([features, action_encoded]).astype(np.float32)
        rewards = df[self.reward_col].values.astype(np.float32)

        return processed, rewards

    def save(self, save_dir: str = 'processor_assets') -> None:
        """保存处理器参数供推理使用"""
        os.makedirs(save_dir, exist_ok=True)
        joblib.dump(self.scaler, os.path.join(save_dir, 'scaler.pkl'))
        joblib.dump(self.feature_columns, os.path.join(save_dir, 'feature_columns.pkl'))
        joblib.dump(self.action_mapping, os.path.join(save_dir, 'action_mapping.pkl'))

    @classmethod
    def load(cls, load_dir: str = 'processor_assets') -> 'PokerDataProcessor':
        """从保存的参数加载处理器"""
        processor = cls()
        processor.scaler = joblib.load(os.path.join(load_dir, 'scaler.pkl'))
        processor.feature_columns = joblib.load(os.path.join(load_dir, 'feature_columns.pkl'))
        processor.action_mapping = joblib.load(os.path.join(load_dir, 'action_mapping.pkl'))
        processor.action_dim = len(processor.action_mapping) if processor.action_mapping else None
        return processor


# ================
# 神经网络模型
# ================
class ActionValueNetwork(nn.Module):
    """
    该类定义了预测 "动作价值" 的神经网络，本质是一个Q 值函数 approximator（近似 Q (s,a)，即状态 s 下采取动作 a 的预期奖励）。
    网络结构：    
    1. 特征提取网络（feature_net）：
        输入：拼接后的特征 + 动作编码（维度 = 特征数 + 动作数）；
        由 2 层线性层组成，搭配正则化机制：
            BatchNorm1d/LayerNorm：缓解梯度消失，加速训练；
            ELU/SiLU：非线性激活函数，增强模型表达能力；
            Dropout(0.3)：随机丢弃 30% 神经元，防止过拟合。
    2. 价值输出头（value_head）：
        将提取的特征映射为一个标量值（动作的预测价值）；
        最终输出通过squeeze()压缩维度，与奖励（标量）对齐。
    """
    def __init__(self, input_dim: int):
        super().__init__()
        self.feature_net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ELU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.SiLU()
        )
        self.value_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.feature_net(x)
        return self.value_head(features).squeeze()


# ================
# 训练系统
# ================
class PokerTrainer:
    """
    该类封装了完整的模型训练流程，包括数据加载、训练循环、验证与早停机制，核心是让模型学习 "特征 - 动作→奖励" 的映射。
    核心功能：
    1. 数据准备（prepare_data）：
        调用PokerDataProcessor处理原始数据，得到模型输入和奖励；
        划分训练集（80%）和验证集（20%），通过DataLoader实现批量加载；
        初始化模型、优化器（AdamW，带权重衰减的 Adam，减轻过拟合）和学习率调度器（ReduceLROnPlateau，验证损失不下降时衰减学习率）。
    2. 训练循环：
        train_epoch：单轮训练逻辑，包括前向传播（预测动作价值）、计算损失（HuberLoss，对异常值更稳健）、反向传播（梯度裁剪防止梯度爆炸）和参数更新。
        validate：在验证集上计算损失和 MAE（平均绝对误差），评估模型泛化能力。
        full_train：完整训练流程，包含：
            早停机制（连续patience轮验证损失不下降则停止，避免过拟合）；
            保存最佳模型（验证损失最小时的权重）和预处理参数。
    """


    def __init__(self, df: pd.DataFrame, model_save_path: str = 'best_model.pth'):
        self.df = df
        self.model_save_path = model_save_path
        self.processor = PokerDataProcessor()
        
        # 设备配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {self.device}")

        # 初始化数据（获取输入维度后再创建模型）
        self.train_loader: Optional[DataLoader] = None
        self.val_loader: Optional[DataLoader] = None
        self.model: Optional[ActionValueNetwork] = None
        self.optimizer: Optional[optim.Optimizer] = None
        self.scheduler: Optional[optim.lr_scheduler._LRScheduler] = None
        self.loss_fn = nn.HuberLoss(delta=1.0)

    def prepare_data(self, batch_size: int = 512, test_size: float = 0.2) -> None:
        """预处理数据并创建数据加载器"""
        x, y = self.processor.process(self.df)
        
        # 划分数据集
        x_train, x_val, y_train, y_val = train_test_split(
            x, y, test_size=test_size, random_state=42
        )

        # 创建Tensor数据集
        train_dataset = TensorDataset(
            torch.tensor(x_train, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.float32)
        )
        val_dataset = TensorDataset(
            torch.tensor(x_val, dtype=torch.float32),
            torch.tensor(y_val, dtype=torch.float32)
        )

        # 创建数据加载器
        self.train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True, num_workers=4
        )
        self.val_loader = DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False, num_workers=4
        )

        # 根据输入维度初始化模型
        input_dim = x.shape[1]
        self.model = ActionValueNetwork(input_dim).to(self.device)
        self.optimizer = optim.AdamW(
            self.model.parameters(), lr=3e-4, weight_decay=1e-5
        )
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5, verbose=True
        )

    def train_epoch(self) -> float:
        """训练单个epoch"""
        if not self.model or not self.optimizer or not self.train_loader:
            raise RuntimeError("请先调用prepare_data()初始化训练资源")

        self.model.train()
        total_loss = 0.0
        
        for batch_x, batch_y in self.train_loader:
            batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
            
            self.optimizer.zero_grad()
            pred = self.model(batch_x)
            loss = self.loss_fn(pred, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            total_loss += loss.item() * batch_x.size(0)
            
        return total_loss / len(self.train_loader.dataset)

    def validate(self) -> Tuple[float, float]:
        """在验证集上评估"""
        if not self.model or not self.val_loader:
            raise RuntimeError("请先调用prepare_data()初始化训练资源")

        self.model.eval()
        total_loss = 0.0
        total_mae = 0.0
        
        with torch.no_grad():
            for batch_x, batch_y in self.val_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                pred = self.model(batch_x)
                loss = self.loss_fn(pred, batch_y)
                mae = torch.abs(pred - batch_y).mean()
                
                total_loss += loss.item() * batch_x.size(0)
                total_mae += mae.item() * batch_x.size(0)
        
        avg_loss = total_loss / len(self.val_loader.dataset)
        avg_mae = total_mae / len(self.val_loader.dataset)
        return avg_loss, avg_mae

    def full_train(self, epochs: int = 100, patience: int = 10) -> None:
        """完整训练流程，带早停机制"""
        self.prepare_data()
        if not self.model:
            raise RuntimeError("模型初始化失败")

        best_loss = float('inf')
        early_stop_counter = 0
        
        # 保存处理器参数
        self.processor.save()
        
        for epoch in range(epochs):
            train_loss = self.train_epoch()
            val_loss, val_mae = self.validate()
            
            # 学习率调度
            self.scheduler.step(val_loss)
            
            # 早停检查
            if val_loss < best_loss:
                best_loss = val_loss
                early_stop_counter = 0
                torch.save(self.model.state_dict(), self.model_save_path)
                print(f"Epoch {epoch+1} - 保存最佳模型 (Val Loss: {val_loss:.4f})")
            else:
                early_stop_counter += 1
                if early_stop_counter >= patience:
                    print(f"早停于Epoch {epoch+1} (连续{patience}轮无改进)")
                    break
            
            print(f"Epoch {epoch+1}/{epochs}")
            print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val MAE: {val_mae:.4f}")


# ================
# 推理决策系统
# ================
class PokerAI:
    """
    该类用于训练完成后的实际决策，核心是基于当前状态特征，预测所有可能动作的价值并选择最优动作。
推理流程：
加载资源：加载训练好的模型权重和PokerDataProcessor参数（确保预处理逻辑与训练时一致）。
特征处理：将输入的状态特征（支持字典、Series、对象格式）转换为 DataFrame，筛选所需特征并标准化。
全动作预测：
为所有可能的动作（基于action_mapping）生成 one-hot 编码；
拼接 "当前特征 + 每个动作的编码"，形成多个输入；
批量预测所有输入的动作价值。
最优决策：选择预测价值最高的动作作为输出。
    
    """


    def __init__(self, model_path: str = 'best_model.pth', processor_dir: str = 'processor_assets'):
        # 加载处理器
        self.processor = PokerDataProcessor.load(processor_dir)
        if not self.processor.action_mapping:
            raise ValueError("处理器未正确加载动作映射")
        
        # 初始化模型
        self.model = self._init_model(model_path)
        
        # 设备配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()

    def _init_model(self, model_path: str) -> ActionValueNetwork:
        """初始化并加载模型权重"""
        # 计算输入维度：特征数 + 动作维度
        feature_dim = len(self.processor.feature_columns) if self.processor.feature_columns else 0
        input_dim = feature_dim + self.processor.action_dim
        model = ActionValueNetwork(input_dim)
        
        # 加载模型权重
        try:
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        except FileNotFoundError:
            raise FileNotFoundError(f"模型文件未找到: {model_path}")
        return model

    def predict(self, features: Union[Dict, pd.Series, object]) -> Tuple[int, np.ndarray]:
        """
        预测最优动作
        参数: features - 包含特征的字典、Series或对象
        返回: (最佳动作, 所有动作的预测价值)
        """
        # 统一特征格式为DataFrame
        if isinstance(features, dict):
            feature_df = pd.DataFrame([features])
        elif isinstance(features, pd.Series):
            feature_df = pd.DataFrame([features])
        else:  # 处理对象类型输入
            feature_df = pd.DataFrame([features.__dict__])
        
        # 筛选所需特征并确保顺序一致
        if self.processor.feature_columns:
            missing_feats = set(self.processor.feature_columns) - set(feature_df.columns)
            if missing_feats:
                raise ValueError(f"缺少必要特征: {missing_feats}")
            feature_df = feature_df[self.processor.feature_columns]
        
        # 标准化特征
        features_scaled = self.processor.scaler.transform(feature_df.values.astype(np.float32))
        
        # 生成所有可能动作的输入
        action_inputs = []
        for action in self.processor.action_mapping.keys():
            # 生成one-hot编码
            action_encoded = np.zeros(self.processor.action_dim, dtype=np.float32)
            action_encoded[self.processor.action_mapping[action]] = 1.0
            # 拼接特征与动作编码
            combined = np.concatenate([features_scaled[0], action_encoded])
            action_inputs.append(combined)
        
        # 批量预测
        with torch.no_grad():
            inputs = torch.tensor(action_inputs, dtype=torch.float32).to(self.device)
            values = self.model(inputs).cpu().numpy()
        
        # 选择最佳动作（原始动作值，非索引）
        action_list = list(self.processor.action_mapping.keys())
        best_action = action_list[np.argmax(values)]
        
        return best_action, values


# ================
# 使用示例
# ================
if __name__ == "__main__":
    # 示例：生成模拟数据
    def generate_sample_data(n_samples: int = 10000, n_features: int = 20) -> pd.DataFrame:
        """生成模拟的扑克游戏数据"""
        # 随机特征
        features = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feat_{i}' for i in range(n_features)]
        )
        # 随机动作（0-2）
        features['action'] = np.random.randint(0, 3, size=n_samples)
        # 模拟奖励（基于特征和动作的函数）
        features['reward'] = (
            0.5 * features['feat_0'] + 
            0.3 * (features['action'] == 1) - 
            0.2 * (features['action'] == 2) + 
            np.random.randn(n_samples) * 0.1
        )
        return features

    # 1. 生成数据并训练模型
    df = generate_sample_data()
    trainer = PokerTrainer(df)
    trainer.full_train(epochs=50)

    # 2. 使用训练好的模型进行推理
    ai = PokerAI()
    
    # 生成测试特征（实际应用中替换为真实游戏状态）
    test_feature = {f'feat_{i}': np.random.randn() for i in range(20)}
    best_action, values = ai.predict(test_feature)
    
    print(f"\n推理结果:")
    print(f"最佳动作: {best_action}")
    print(f"各动作预测价值: {values}")
