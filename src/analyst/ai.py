import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd


# =====================
# 数据预处理与特征工程
# =====================
class PokerDataProcessor:
    def __init__(self, feature_columns=None):
        self.feature_columns = feature_columns
        self.action_col = 'action'
        self.reward_col = 'reward'
        self.scalers = {
            'features': StandardScaler(),
            'action': StandardScaler(with_mean=False)  # 动作不需要中心化
        }

    def process(self, df):
        """处理原始数据框"""
        if self.feature_columns is None:
            # 排除已知的非特征列
            self.feature_columns = [col for col in df.columns
                                    if col not in [self.action_col, self.reward_col]]
        # 提取动态特征
        features = df[self.feature_columns].values.astype(np.float32)
        num_features = features.shape[1]  # 动态获取特征数
        print('动态获取特征数:', num_features)
        # 特征标准化
        features = self.scalers['features'].fit_transform(features)

        # 动作编码（扩展为三维空间）
        actions = df[self.action_col].values.reshape(-1, 1)
        action_encoded = np.zeros((len(actions), 3), dtype=np.float32)
        action_encoded[np.arange(len(actions)), actions.squeeze()] = 1.0

        # 拼接特征矩阵
        processed = np.hstack([features, action_encoded]).astype(np.float32)
        rewards = df[self.reward_col].values.astype(np.float32)

        return processed, rewards


# ================
# 神经网络模型
# ================
class ActionValueNetwork(nn.Module):
    def __init__(self, input_dim=10):
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

    def forward(self, x):
        features = self.feature_net(x)
        return self.value_head(features).squeeze()


# ================
# 训练系统
# ================
class PokerTrainer:
    def __init__(self, df):
        print("NumPy 版本:", np.__version__)

        # 加载数据
        self.df = df
        self.processor = PokerDataProcessor()

        # 初始化模型
        self.model = ActionValueNetwork()
        self.optimizer = optim.AdamW(self.model.parameters(), lr=3e-4, weight_decay=1e-5)
        self.loss_fn = nn.HuberLoss(delta=1.0)  # 鲁棒回归损失

        # 设备配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)


    def prepare_data(self):
        """数据预处理与划分"""
        x, y = self.processor.process(self.df)
        x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2, random_state=42)

        # 转换为张量
        self.train_data = (
            torch.tensor(x_train, dtype=torch.float32).to(self.device),
            torch.tensor(y_train, dtype=torch.float32).to(self.device))
        self.val_data = (
            torch.tensor(x_val, dtype=torch.float32).to(self.device),
            torch.tensor(y_val, dtype=torch.float32).to(self.device))

    def train_epoch(self, batch_size=512):
        """训练单个epoch"""
        self.model.train()
        x, y = self.train_data
        indices = torch.randperm(len(x))

        total_loss = 0
        for i in range(0, len(x), batch_size):
            batch_idx = indices[i:i + batch_size]
            batch_x = x[batch_idx]
            batch_y = y[batch_idx]

            self.optimizer.zero_grad()
            pred = self.model(batch_x)
            loss = self.loss_fn(pred, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()

            total_loss += loss.item() * len(batch_idx)
        return total_loss / len(x)

    def validate(self):
        """验证集评估"""
        self.model.eval()
        with torch.no_grad():
            x, y = self.val_data
            pred = self.model(x)
            loss = self.loss_fn(pred, y)
            mae = torch.abs(pred - y).mean()
        return loss.item(), mae.item()

    def full_train(self, epochs=100):
        """完整训练流程"""
        self.prepare_data()

        best_loss = float('inf')
        for epoch in range(epochs):
            train_loss = self.train_epoch()
            val_loss, val_mae = self.validate()

            # 保存最佳模型
            if val_loss < best_loss:
                best_loss = val_loss
                torch.save(self.model.state_dict(), 'best_model.pth')

            print(f"Epoch {epoch + 1}/{epochs}")
            print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val MAE: {val_mae:.2f}")


# ================
# 推理决策系统
# ================
class PokerAI:
    def __init__(self):
        self.model = ActionValueNetwork()
        self.model.load_state_dict(torch.load('ai/best_model.pth'))
        self.model.eval()
        self.processor = PokerDataProcessor()

        # 设备配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def predict(self, feature):
        """
        输入: 原始特征数组 (20维)
        输出: 最优动作 (0/1/2), 预测收益
        """
        # 获取特征值
        features = pd.DataFrame(feature.__dict__)
        features = features.astype(np.float32)  # 输入特征强制转换

        # 标准化特征
        features = self.processor.scalers['features'].transform([features])[0]

        # 生成三个动作的输入
        action_inputs = []
        for action in [0, 1, 2]:
            action_encoded = np.zeros(3)
            action_encoded[action] = 1
            combined = np.concatenate([features, action_encoded])
            action_inputs.append(combined)

        # 批量预测
        with torch.no_grad():
            inputs = torch.tensor(action_inputs, dtype=torch.float32).to(self.device)
            values = self.model(inputs).cpu().numpy()

        # 选择最佳动作
        best_action = np.argmax(values)

        return best_action
