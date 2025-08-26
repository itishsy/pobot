### **AI特征工程**

特征工程是AI扑克智能体的灵魂。以下特征应被实时计算并作为决策模型的输入。

#### **A. 个人手牌与牌面特征 (Hand & Board Strength)**
1.  **Hand Strength**:
    - `HAND_EQUITY`: 当前手牌对抗对手预估范围的胜率（0.0-1.0）。
    - `HAND_CATEGORY`: 手牌分类（高牌、对子、两对、顺子听牌、同花听牌、成牌等）。
    - `HAND_POTENTIAL`: 未来发展成强牌的能力（如听牌强度）。
2.  **Board Texture**:
    - `BOARD_WETNESS`: 牌面的联动性（高联动性=湿，低=干）。听牌多的牌面是湿的。
    - `BOARD_PAIRED`: 牌面是否有对子。
    - `BOARD_SUITED`: 牌面是否三张或以上同花。
    - `BOARD_STRAIGHT_DRAW`: 牌面是否存在可能的顺子听牌。

#### **B. 局面动态特征 (Game Dynamic)**
3.  **Position**:
    - `POSITION_ABS`: 绝对位置（按钮位=0， cutoff=1, 枪口=5）。
    - `POSITION_REL`: 相对于对手的位置（是在有利位还是不利位）。
4. **Pot & Stack**:
    - `POT_ODDS`: 底池赔率 = (跟注金额) / (底池总额 + 跟注金额)。
    - `SPR` (Stack-to-Pot Ratio): 有效筹码量 / 当前底池大小。决定后续回合的承诺度。
    - `EFFECTIVE_STACK`: 我方与对手之间较小的筹码量。
5.  **Action History**:
    - `PREFLOP_RAISER`: 谁是翻前加注者。
    - `AGGRESSOR`: 当前回合的最后一个激进者（加注/再加注的人）。
    - `NUMBER_RAISES`: 当前回合已发生的加注次数。

#### **C. 对手特征 (Opponent Modeling) - 最为关键**
6.  **Preflop Stats**:
    - `OPP_VPIP`: 入局率。
    - `OPP_PFR`: 翻前加注率。
    - `OPP_3BET%`: 3Bet频率。
    - `OPP_FOLD_TO_3BET%`: 面对3Bet的弃牌率。
7.  **Postflop Stats**:
    - `OPP_AGG_FREQ (AF)`: 攻击频率（加注+下注次数） / （跟注次数）。
    - `OPP_CBET%`: 作为翻前加注者，在翻牌圈持续下注的频率。
    - `OPP_FOLD_TO_CBET%`: 面对持续下注的弃牌率。
    - `OPP_CHECK_RAISE%`: 过牌-加注频率。
8.  **Tendency Profiles**:
    - `TAG` (Tight-Aggressive): 紧凶型。
    - `LAG` (Loose-Aggressive): 松凶型。
    - `LP` (Loose-Passive): 松弱型（跟注站）。
    - `TP` (Tight-Passive): 紧弱型（岩石）。
    - 这些不是单一特征，而是以上统计数据的综合画像。

#### **D. 资金与元特征 (Meta-Features)**
9.  **Bankroll**:
    - `BUYIN_LEVEL`: 当前买入相对于总资金的比例。
10. **Game Flow**:
    - `WINNING_STREAK` / `LOSING_STREAK`: 近期连胜/连败手数，用于情绪模拟和反剥削（防止被对手利用情绪化打法）。

### **如何使用这些特征：**
- **基于规则的AI**：在决策树中，使用这些特征作为`if-then-else`条件来判断。
    *例如：`if SPR < 4 and HAND_STRENGTH > 0.65: then ACTION_RAISE`*
- **机器学习AI**：将这些特征构建成一个**特征向量**（Feature Vector），输入到一个模型（如XGBoost或神经网络）中，该模型输出动作的概率分布或直接的Q值。