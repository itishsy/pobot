
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

