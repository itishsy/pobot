import random
from config.gg import BB
from models.game_feature import GameFeature


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


def eval_win_rate(cond, args):
    for co in cond.children:
        if not co.children:
            return eval(co.exp.strip())
        elif eval(co.exp.strip(), args):
            return eval_win_rate(co, args)


class Strategy:

    def __init__(self):
        self.preflop_strategy = self.load('strategy/preflop')
        self.flop_strategy = self.load('strategy/flop')
        # self.turn_strategy = self.load('turn')
        # self.river_strategy = self.load('river')

    @staticmethod
    def load(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                line = file.readline()
                cond = Cond(line)
                while line:
                    line = file.readline()
                    cond.append_child(line.replace('\t', ''), line.count('\t'))
            return cond
        except FileNotFoundError:
            print(f"{file_name} strategy file not found")

    def predict(self, feature):
        """
        預測策略：
        1. 計算牌面濕潤程度：wet.  args: wet_high、wet_pair、wet_straight、wet_flush
        2. 計算玩家的成牌概率: rwin.  args: wet、c_bet、c_raise、b_bet
        3. 計算勝率：win = strength * rate.  args: stage、pos、strength、rwin、players
        4. 計算行為：action，raised. args，計算ev最大化應該採取的行為、
        """
        args = feature.to_dict()
        args['r'] = round(random.uniform(0, 1), 2)
        args['wet'] = self._wet(feature)
        if feature.stage == 0:
            win_rate = eval_win_rate(self.preflop_strategy, args)
        elif feature.stage == 1:
            win_rate = eval_win_rate(self.flop_strategy, args)
        elif feature.stage == 2:
            win_rate = eval_win_rate(self.flop_strategy, args)
        else:
            win_rate = eval_win_rate(self.flop_strategy, args)
        win = round(feature.strength * random.uniform(win_rate[0], win_rate[1]), 2)
        bet, ev = self._best_ev(feature, win)
        raised = 0
        calls = feature.calls
        if bet < calls:
            action = 'fold'
        elif bet == calls:
            action = 'call' if calls > 0 else 'check'
        else:
            if calls > 0:
                bet_dif = bet / calls
                if bet_dif < 2:
                    action = 'call'
                else:
                    action = 'raise'
                    if bet_dif > 10:
                        raised = 4
                    elif bet_dif >= 5:
                        raised = 3
                    else:
                        raised = 2
            else:
                if bet < BB * 2:
                    action = 'check'
                else:
                    action = 'raise'
                    raised = 3
        return {'win': win, 'bet': bet, 'ev': ev, 'action': action, 'raised': raised}

    @staticmethod
    def _wet(feature):
        if feature.stage == 1:
            if feature.wet_straight > 0 or feature.wet_flush > 0:
                return 2
            return max(feature.wet_high,feature.wet_pair)
        else:
            if feature.wet_straight < 1 and feature.wet_flush < 1 and feature.wet_pair < 2:
                return max(0, feature.wet_high-1)
            return max(feature.wet_high, feature.wet_pair)

    @staticmethod
    def _win_rate(feature):
        """
        TODO： 勝率 = 手牌成牌概率
        """
        factor = 1
        strength = feature.strength
        stage = feature.stage
        pots = feature_dict['pots']
        players = feature_dict['players']
        if stage == 0:
            """ 
            翻牌前调节因子：底池大小、人数越多
            """
            if strength > 0.8:
                # 强牌，底池越大勝率增加
                if pots > 20:
                    factor = factor * random.uniform(1.05, 1.1)
            else:
                # 中间牌，入池人数越多勝率增加
                if pots > 20:
                    factor = factor * random.uniform(0.85, 0.95)
                if players > 2:
                    factor = factor * random.uniform(0.85, 0.95)
        else:
            """ 
            翻牌后调节因子：牌面湿润度、玩家下注行为、玩家手牌范围赢率rwin
            """
            factor = 0.9 ** stage
            # 玩家下注行为
            if feature_dict['c_bet'] > 0:
                factor = factor * random.uniform(0.8 ** feature_dict['c_bet'], 0.9 ** feature_dict['c_bet'])
            if feature_dict['b_bet'] > 0:
                factor = factor * random.uniform(0.8 ** feature_dict['b_bet'], 0.9 ** feature_dict['b_bet'])
            if feature_dict['c_raise'] > 0:
                factor = factor * random.uniform(0.8 ** feature_dict['c_raise'], 0.9 ** feature_dict['c_raise'])
            # 牌面湿润度
            if feature_dict['wet'] > 1:
                factor = factor * random.uniform(0.85, 0.95)
            elif feature_dict['wet'] < 1 and strength > 0.6:
                factor = factor * random.uniform(1, 1.1)
            # 玩家手牌范围赢率
            # if self.rwin > 0.65:
            #     factor = factor * random.uniform(0.85, 0.95)
            # elif self.rwin < 0.45:
            #     factor = factor * random.uniform(1, 1.1)

        win_rate = min(round(strength * factor, 2), 1)
        # 修复bug：手牌强度没加强，赢率增加
        # if len(states) > 2:
        #     pre_strength = states[-2].feature.strength
        #     pre_win_rate = states[-2].win
        #     if pre_strength > strength and pre_win_rate < win_rate:
        #         win_rate = round(pre_win_rate * pre_strength / strength, 2)
        return win_rate

    @staticmethod
    def _best_ev(feature, win_rate):
        """ EV计算公式
        EV = 对手弃牌率 × 底池价值 + (对手跟注率 × 赢率 × 潜在收益) - (对手跟注率 × 输率 × 投入成本)
        """
        pots = feature.pots
        calls = feature.calls
        best_ev = {'ev': 0, 'bet': 0}
        if calls > 0:
            """計算跟注的ev"""
            ev = (win_rate * pots - (1 - win_rate) * calls)
            best_ev['ev'] = round(ev, 2)
            best_ev['bet'] = calls
            print('calls:', calls, '; cev:', ev)

        if win_rate > 0.6:
            """計算加注的ev"""
            if feature.stage == 0 and pots < 10 and feature.pos > 1:
                fold_rate = 0.2
            elif feature.players > 1 or feature.c_bet > 0 or feature.b_bet > 0 or feature.c_raise > 0:
                fold_rate = random.uniform(0.05, 0.1)
            else:
                fold_rate = random.uniform(0.15, 0.2)

            # 加注量，相对底池占比
            bet_radios = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
            for br in bet_radios:
                bet_amt = round(br * pots, 2)
                if bet_amt > calls:
                    b_ev = round((fold_rate * pots +
                                  (1 - fold_rate) * (win_rate * (pots + bet_amt)) -
                                  (1 - win_rate) * bet_amt), 2)
                    print('bet:', bet_amt, '(', br, '); ev:', b_ev)
                    if b_ev > best_ev['ev']:
                        best_ev['ev'] = b_ev
                        best_ev['bet'] = bet_amt
        return best_ev['bet'], best_ev['ev']


if __name__ == '__main__':
    fea = GameFeature()
    fea.stage = 0
    fea.win = 0.8
    fea.calls = 3
    fea.b_bet = 2
    st = Strategy()
    st.predict(fea.to_dict())
    print(f'action={fea.action}')
