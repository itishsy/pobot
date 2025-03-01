class AdversarialTrainer:
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