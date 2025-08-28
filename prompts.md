# 项目：No-Limit Texas Hold'em 6-Max Cash Game AI 智能体

## 1. 项目概述与技术栈
- **目标**：开发一个用于线上6人桌NLH现金局的AI智能体。其核心目标是实现长期期望价值（EV）的最大化。
- **技术栈**：Python 3.11+, PyPokerEngine (或自定义游戏引擎), NumPy, Pandas, Scikit-Learn, PyTorch/TensorFlow (用于高级模型), 基于规则的系统与机器学习相结合。

## 2. 核心架构设计
我们的AI采用**模块化架构**，核心模块包括：
- **游戏状态解析器 (Game State Parser)**：解析来自游戏引擎（如PyPokerEngine）的JSON状态，将其转换为内部表示。
- **智能体内核 (Agent Core)**：主决策循环。
- **手牌强度计算器 (Hand Strength Evaluator)**：使用蒙特卡洛模拟或预计算 equity 表来评估当前手牌的胜率。
- **博弈论最优近似器 (GTO Approximator)**：包含一个范围模型和简化博弈树，用于提供基于GTO的基准策略。
- **剥削性调整模块 (Exploitative Adjuster)**：根据对手模型偏离GTO基准的程度，进行动态调整。
- **对手建模器 (Opponent Modeler)**：实时追踪并更新对手的统计数据（VPIP, PFR, AF, 3Bet%, Fold to CBet% 等）。
- **资金管理模块 (Bankroll Manager)**：根据资金动态调整策略激进程度（可选）。

## 3. 决策流程 (AI::decide(action, game_state))
智能体的决策函数应遵循以下逻辑流程：

1.  **解析状态**：从 `game_state` 中提取所有相关信息。
2.  **更新对手模型**：根据当前回合的行动，更新相关玩家的统计数据。
3.  **计算基础胜率 (Equity)**：计算我方手牌对抗对手预估范围的胜率。
4.  **构建决策树**：枚举所有合法动作（fold, call, raise, all-in）及其预期的EV。
5.  **EV 计算**：
    - **Fold EV**：已知（即当前已投入的筹码损失）。
    - **Call EV**： = (Pot + Bet to Call) * Equity - Bet to Call
    - **Raise EV**：更复杂，需模拟对手可能的反应（Fold/Call/Raise），并加权平均其EV。严重依赖对手模型。
6.  **决策**：选择具有最高期望EV的动作。所有EV计算必须考虑当前底池赔率、隐含赔率和反向隐含赔率。

## 4. 代码风格与规范
- 使用清晰的类型提示（Type Hints）。
- 为所有复杂函数编写详细的文档字符串（Docstrings），解释输入、输出和逻辑。
- 变量名和函数名使用描述性的蛇形命名法（e.g., `calculate_pot_odds`, `current_pot_size`）。
- 将常量（如筹码量、位置枚举）定义在配置文件或常量类中。

## 5. 关键数据结构示例（Python）
```python
from typing import List, Dict, Optional

class PlayerModel:
    def __init__(self):
        self.vpip: float = 0.0 # Voluntarily Put $ in Pot %
        self.pfr: float = 0.0  # Pre-Flop Raise %
        self.af: float = 0.0   # Aggression Frequency
        # ... other stats

class GameState:
    def __init__(self):
        self.pot: int = 0
        self.community_cards: List[Card] = []
        self.legal_actions: List[Action] = []
        self.current_bet: int = 0
        self.my_stack: int = 0
        self.opponent_stacks: Dict[str, int] = {}
        self.history: List[Action] = []
        self.dealer_button_pos: int = 0
        self.my_position: int = 0
        self.opponent_models: Dict[str, PlayerModel] = {} # Keyed by player UUID