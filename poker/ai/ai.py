import torch
import torch.nn as nn
from poker.ai.adaptive_learner import AdaptiveLearner
from poker.ai.bankroll_manager import BankrollManager
from poker.ai.strategic_analyst import StrategicAnalyst


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
            if action == 2:  # raise
                bet_size = self.bankroll.get_bet_size(
                    self.learner.policy_net(torch.FloatTensor(processed_state))[0].detach().numpy(),
                    game_state.pot)
                return 'raise', bet_size
            else:
                return action, 0
        else:
            return self.analyst.get_action(game)

    def start_learn(self, final_reward):
        episode_data = []
        self.learner.learn_from_episode(episode_data)
        self.bankroll.update(final_reward)

