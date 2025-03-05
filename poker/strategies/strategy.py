import poker.game
from poker.card import Hand, suits
from poker.strategies.sorted_hands import hands_win_rate
from poker.config import BB
from decimal import Decimal
from itertools import combinations
import random
from poker.models.hand_score import HandScore


def fetch_by_level(cd, le):
    if len(cd.code) == le:
        return cd
    else:
        for c in reversed(cd.children):
            return fetch_by_level(c, le)


class Cond:
    code = '0'
    exp = ''
    children = []

    def __init__(self, exp):
        self.exp = exp
        self.children = []

    def append_child(self, exp, level):
        parent = fetch_by_level(self, level)
        if parent:
            cd = Cond(exp)
            cd.code = '{}{}'.format(parent.code, len(parent.children) + 1)
            cd.children = []
            parent.children.append(cd)


def eval_cond(cond, args):
    for co in cond.children:
        if not co.children:
            return co.exp.strip()
        if eval(co.exp, args):
            return eval_cond(co, args)


class Strategy:

    actions = 'strategies/actions.txt'
    ranges = 'strategies/ranges.txt'

    def __init__(self):
        self.action_cond = None
        self.range_cond = None
        self.action_args = {}
        self.range_args = {}
        try:
            with open(self.actions, 'r', encoding='utf-8') as file:
                line = file.readline()
                self.action_cond = Cond(line)
                while line:
                    line = file.readline()
                    self.action_cond.append_child(line.replace('\t', ''), line.count('\t'))
            with open(self.ranges, 'r', encoding='utf-8') as file:
                line = file.readline()
                self.range_cond = Cond(line)
                while line:
                    line = file.readline()
                    self.range_cond.append_child(line.replace('\t', ''), line.count('\t'))
        except FileNotFoundError:
            print(f"策略文件不存在,忽略")

    def predict_action(self, game):
        hand = Hand(game.card1, game.card2)
        if game.card3:
            hand.add_board(game.card3)
            hand.add_board(game.card4)
            hand.add_board(game.card5)
            if game.card6:
                hand.add_board(game.card6)
                if game.card7:
                    hand.add_board(game.card7)

        call = game.sections[-1].call
        pot = game.sections[-1].pool
        seat = game.seat

        if game.stage == 'PreFlop':
            """
            (1) hand_score>80，有raise，无call和fold选项。 raise随机选择bet大码
            (2) 80>hand_score>70，有raise、call, 无fold。 call量为中大码，选择call。 否则随机选择raise中大码
            (3) 70>hand_score>60，有raise、call、fold。 有call，按ev计算选择call和fold； 无call，随机选择raise中码
            (4) 60>hand_score>50，有call、fold，有条件raise。 ev计算call及fold，有位置时，min-raise随机bb(2,4)
            (5) hand_score<50, 有fold，有条件call。 有位置时，min-raise随机bb(2,4)
            """
            score = game.hand_score
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
                if cev == 0 and seat == 6 and random.randint(1, 3) == 1:
                    return 'raise:{}'.format(random.randint(1, 2))
            elif 0.6 > score >= 0.55:
                # 中等牌，避免参与过大的底池
                if pot < 30 * BB:
                    if cev > 0:
                        return 'call'
                    if cev == 0 and seat == 6 and random.randint(1, 3) == 1:
                        return 'raise:{}'.format(random.randint(1, 2))
            elif 0.55 < score < 0.5:
                # 弱牌，小底池有位置可参与
                if pot < 20 * BB and seat in (1, 2, 5, 6) and cev > 0 and random.randint(1, 3) == 1:
                    return 'call'
        else:
            score = hand.get_score()
            opponent_ranges = self.predict_ranges(game)
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
    def predict_ranges(game):
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

    def nuts_rate(self, game):
        """
        成牌概率。 一般来讲，成牌大小与下注金额相关。暂未考虑诈唬
        :param game:
        :return:
        """
        pass


def test_strategy(code):
    from poker.game import Game, Section
    sections = Section.select().where(Section.game_code == code).order_by(Section.id)
    strategy = Strategy()
    game = None
    if len(sections) > 0:
        idx = 0
        for sec in sections:
            if idx == 0:
                game = Game(sec)
                print(game.get_info())
            else:
                game.append_section(sec)
            act = strategy.predict_action(game)
            print("{} : hand score --> {} action --> {}".format(
                game.stage, game.sections[-1].hand_score if game.stage == 'PreFlop' else game.sections[-1].hand_strength, act))
            idx = idx + 1


if __name__ == '__main__':
    test_strategy('20250208180018')
