import torch
import torch.nn as nn
from poker.ai.learner import AdaptiveLearner
from poker.ai.bankroll import BankrollManager
from poker.ai.analyst import StrategicAnalyst


class PokerAI:
    def __init__(self, drl=True):
        self.drl = drl
        self.learner = AdaptiveLearner()
        self.analyst = StrategicAnalyst()
        self.bankroll = BankrollManager()
        self.game_state = None

    def eval_action(self, game):
        if self.drl:
            game_state = game.states[-1]
            # 获取当前处理后的状态
            processed_state = self.learner.state_processor.process(game_state)
            # 获取AI决策
            action, predicted_value = self.learner.get_action(game_state)
            # 资金管理调整下注量
            bet_size = 0
            if action == 2:  # raise
                bet_size = self.bankroll.get_bet_size(
                    self.learner.policy_net(torch.FloatTensor(processed_state))[0].detach().numpy(),
                    game_state.pot)
                action = 'raise'
        else:
            action, bet_size = self.analyst.calculate_action(game)
        return action, bet_size

    def start_learn(self, final_reward):
        episode_data = []
        self.learner.learn_from_episode(episode_data)
        self.bankroll.update(final_reward)

