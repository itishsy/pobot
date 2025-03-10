from poker.models.game import Game
from poker.models.hand_score import HandScore
import random


class Strategy:

    def eval_action(self, game):
        stage = game.states[-1].stage
        if stage == 0:
            score = HandScore.get_score(game.hand[0], game.hand[1])
            cev = pot * score - (100 - score) * call
            if score >= 0.8:
                # 超强牌，造大底池
                if pot < 4 * BB:
                    return 'raise:{}'.format(random.randint(2, 4))
                return 'raise:{}'.format(random.randint(4, 10))
            elif 0.8 > score >= 0.7:
                # 强牌，控制底池到合适的大小
                if call > 3 * BB:
                    return 'call'
                return 'raise:{}'.format(2, 4)
            elif 0.7 > score >= 0.6:
                # 中强牌，控制底池，避免参与过大的底池
                if call < 2 * BB:
                    return 'raise:{}'.format(random.randint(1, 2))
                if 2 * BB <= call <= 10 * BB or cev > 0:
                    return 'call'
                if cev == 0 and position == 6 and random.randint(1, 3) == 1:
                    return 'raise:{}'.format(random.randint(1, 2))
            elif 0.6 > score >= 0.55:
                # 中等牌，避免参与过大的底池
                if pot < 30 * BB:
                    if cev > 0:
                        return 'call'
                    if cev == 0 and position == 6 and random.randint(1, 3) == 1:
                        return 'raise:{}'.format(random.randint(1, 2))
            elif 0.55 < score < 0.5:
                # 弱牌，小底池有位置可参与
                if pot < 20 * BB and position in (1, 2, 5, 6) and cev > 0 and random.randint(1, 3) == 1:
                    return 'call'
        else:
            opponent_ranges = self.eval_ranges(game)
            win_rate = hand.win_rate(opponent_ranges)
            raise_amt = pot * win_rate / (1 - win_rate)
            if raise_amt >= call:
                raise_num = int(raise_amt/call)
                if raise_num == 0:
                    return 'call'
                # 随机选择raise或check。score越大，raise的机率越大
                if random.randint(1, 100) > (100 - score):
                    return 'raise:{}'.format(random.randint(1, raise_num))
        return 'check' if call == 0 else 'fold'


    @staticmethod
    def eval_ranges(game):
        """
        手牌范围。评估翻牌前的手牌范围。跟底池大小、玩家行为有关。
        :param game:
        :return:
        """
        player_pre_act = 'raise、call、3bet、check'   # 翻牌前行动。加注通常表示较强的手牌，而跟注可能意味着中等或投机性手牌。
        player_flop_act = '持续bet、check-raise'   # 翻牌后行动。
        player_balance = 100    # 筹码量。 短筹码玩家倾向于玩得更紧，而深筹码玩家可能更激进，尝试利用筹码优势进行诈唬或价值下注。
        player_amt = 6      # 翻牌后下注尺度。大额下注通常表示强牌或诈唬,小额下注可能意味着中等牌力或试探性下注
        player_style = '0, 1, 2'  # 历史行为。 紧凶、松凶、被动。紧凶玩家加注时通常有强牌，而松凶玩家可能用更宽的范围加注
        board_style = '单张成顺、单张成花、卡顺、三张花、'   # 牌面结构。 湿润牌面下注，对手可能有更多听牌或成牌
        pot_bb = 2
        for i in range(len(game.sections)):
            if game.sections[i].stage == 'PreFlop':
                pot_bb = int(game.sections[-1].pool / BB)
        if 1 < pot_bb <= 3:
            opponent_range = HandScore.get_ranges(0.2, 0.6)
        elif 3 < pot_bb <= 10:
            opponent_range = HandScore.get_ranges(0.4, 0.9)
        elif 10 < pot_bb <= 50:
            opponent_range = HandScore.get_ranges(0.5, 0.9)
        else:
            opponent_range = HandScore.get_ranges(0.55, 0.9)
        return opponent_range