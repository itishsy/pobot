class AdversarialTrainer:
    """
    graph TD
    A[开始新牌局] --> B[获取OCR状态]
    B --> C{是否终局?}
    C -->|否| D[状态特征工程]
    D --> E[DRL模型推理]
    E --> F[资金管理调整]
    F --> G[执行动作]
    G --> H[存储经验]
    H --> B
    C -->|是| I[计算最终收益]
    I --> J[蒙特卡洛学习]
    J --> K[更新目标网络]
    K --> L[调整资金状态]
    L --> M{继续训练?}
    M -->|是| A
    M -->|否| N[结束]
    """

    def __init__(self, main_ai, adversary_ai):
        self.main = main_ai
        self.adversary = adversary_ai

    def train_round(self):
        # 主AI与对手AI对抗
        main_states, adv_states = play_heads_up()

        # 交替更新两个AI
        self.main.learn_from_episode(main_states)
        self.adversary.learn_from_episode(adv_states)

        # 交换角色继续训练
        main_states, adv_states = play_heads_up(role_swap=True)
        self.main.learn_from_episode(adv_states)
        self.adversary.learn_from_episode(main_states)