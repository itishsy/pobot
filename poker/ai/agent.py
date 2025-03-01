
# 系统集成使用示例
if __name__ == "__main__":
    learner = AdaptiveLearner()
    bankroll = BankrollManager()

    # 模拟牌局循环
    for episode in range(1000):
        game_state = initialize_game()  # 从OCR获取当前状态
        episode_data = []

        while not game_state['terminal']:
            # 获取当前处理后的状态
            processed_state = learner.state_processor.process(game_state)

            # 获取AI决策
            action, predicted_value = learner.get_action(game_state)

            # 资金管理调整下注量
            if action == 2:  # raise
                bet_size = bankroll.get_bet_size(
                    learner.policy_net(torch.FloatTensor(processed_state))[0].detach().numpy(),
                    game_state['pot']
                )
                execute_action('raise', bet_size)
            else:
                execute_action(['fold', 'call'][action])

            # 存储过渡状态
            next_state = get_updated_state()
            reward = calculate_immediate_reward()
            episode_data.append({
                'state': game_state,
                'action': action,
                'reward': reward,
                'next_state': next_state
            })

            game_state = next_state

        # 牌局结束后学习
        final_reward = calculate_final_profit()
        episode_data[-1]['reward'] += final_reward
        learner.learn_from_episode(episode_data)
        bankroll.update(final_reward)