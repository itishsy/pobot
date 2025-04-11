from models.base_model import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
import json
import copy
from config import SB, BB
from decimal import Decimal
from models.card import HandScore


class GameState(BaseModel):
    class Meta:
        table_name = 'game_state'

    id = AutoField()
    code = CharField()
    hand = CharField()
    position = IntegerField(null=True)
    stage = IntegerField(null=True)
    stack = FloatField(null=True)
    pot = FloatField(null=True)
    board = CharField(null=True)
    call = FloatField(null=True)
    action = CharField(null=True)
    strength = CharField(null=True)
    win_rate = FloatField(null=True)
    players = TextField(null=True)
    player1 = TextField(null=True)
    player2 = TextField(null=True)
    player3 = TextField(null=True)
    player4 = TextField(null=True)
    player5 = TextField(null=True)


class Player:
    name = None
    position = None
    stack = 0.0
    action = None
    amount = 0.0
    active = None

    def __init__(self, name, position, stack, action='pending', active=None, amount=None):
        self.name = name
        self.position = position
        self.stack = stack
        self.action = action
        self.amount = amount
        if active is None:
            self.active = True if name else False
        else:
            self.active = active

    def to_dict(self):
        return {
            'name': self.name,
            'position': self.position,
            'stack': self.stack,
            'action': self.action,
            'amount': self.amount,
            'active': self.active
        }


class State:
    code = None

    hand = []
    board = []
    position = None
    stack = None
    pot = None
    stage = None
    call = None
    action = None
    bet = None
    reward = None
    strength = None
    win_rate = None
    call_ev = None
    raise_ev = None
    players = []

    def to_dict(self):
        return {
            'hand': self.hand,
            'board': self.board,
            'position': self.position,
            'stack': self.stack,
            'pot': self.pot,
            'stage': self.stage,
            'call': self.call,
            'action': self.action,
            'reward': self.reward,
            'players': [obj.to_dict() for obj in self.players]
        }

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player

    def active_players(self):
        active_players = [p for p in self.players if p.active == 1]
        return sorted(active_players, key=lambda x: x.position)


class Game(BaseModel):
    class Meta:
        table_name = 'game'

    id = AutoField()
    code = CharField()
    hand = CharField()
    position = IntegerField(null=True)
    stack = FloatField(null=True)
    reward = FloatField(null=True)

    states = []
    opponent_pre_flop_ranges = []
    # @property
    # def states(self):
    #     """反序列化存储的JSON数据为State对象集合"""
    #     return [State.from_dict(d) for d in json.loads(self.state_data or '[]')]
    #
    # @states.setter
    # def states(self, value):
    #     """序列化State对象集合为JSON存储"""
    #     self.state_data = json.dumps([obj.to_dict() for obj in value] if value else [])

    def add_state(self, state):
        if state.hand != self.hand or state.position != self.position:
            print('------------------new game:', state.stack, ' ------------------')
            if self.hand is not None:
                self.persist(state.stack)
            self.states.clear()
            self.opponent_pre_flop_ranges.clear()
            self.code = datetime.now().strftime('%Y%m%d%H%M%S')
            self.hand = state.hand
            self.position = state.position
            self.stack = state.stack
            init_state = copy.deepcopy(state)
            init_state.code = self.code
            init_state.stage = 0
            init_state.pot = SB + BB
            init_state.players.clear()
            for sp in state.players:
                if sp.position == 0:
                    action = 'sb'
                    stack = round(sp.stack + SB, 2)
                elif sp.position == 1:
                    action = 'bb'
                    stack = round(sp.stack + BB, 2)
                else:
                    action = 'pending'
                    stack = round(sp.stack + sp.amount, 2)
                init_state.players.append(Player(sp.name, sp.position, stack, action=action, active=True))
            self.states.append(init_state)

        pre_state = self.states[-1]
        if state.stage != pre_state.stage or state.pot != pre_state.pot:
            # 计算玩家action, 追加最新state
            state.code = self.code
            active_players = state.active_players()
            pending_players = [p for p in pre_state.players if p.action == 'pending']
            for pp in pending_players:
                gp = state.get_player(pp.name)
                if gp:
                    pp.action = 'call'
                else:
                    pp.action = 'fold'

            # self.set_players_state(state)
            self.states.append(state)

    def set_players_state(self, new_state):
        pre_state = self.states[-1]
        dif_pot = new_state.pot - pre_state.pot
        i_bet = -1
        i_bet_amount = 0.0
        new_state.players.sort(key=lambda x: x.amount, reverse=True)
        max_bet = new_state.players[0].amount
        min_bet = new_state.players[4].amount
        for i in range(5):
            if pre_state.players[i].action == 'fold' or pre_state.players[i].active == 0:
                new_state.players[i].active = 0
                continue

            if new_state.players[i].active == 0:
                new_state.players[i].action = 'fold'
                continue

            dif_stack = pre_state.players[i].stack - new_state.players[i].stack
            if dif_pot > 0 and dif_stack == 0:
                # 底池增加，玩家码量无变化
                new_state.players[i].action = 'fold'
                continue

            if dif_pot == 0:
                new_state.players[i].action = 'check'
                continue

            if dif_pot == dif_stack:
                # 底池与玩家码量变化相等，一家下注
                new_state.players[i].action = 'bet'
                new_state.players[i].amount = dif_stack
                continue

            # 底池大于玩家码量变化。能整除，说明前bet+后call，不能整除，说明前bet+后raise. 会存在误差，先忽略
            if i_bet < 0:
                i_bet = i
                i_bet_amount = dif_stack
                new_state.players[i].action = 'bet'
                new_state.players[i].amount = dif_stack
            else:
                if dif_stack > i_bet_amount:
                    i_bet = i
                    i_bet_amount = dif_stack
                    new_state.players[i].action = 'raise'
                    new_state.players[i].amount = dif_stack
                elif dif_stack < i_bet_amount:
                    new_state.players[i].action = 'bet'
                    new_state.players[i].amount = dif_stack
                    new_state.players[i_bet].action = 'raise'
                else:
                    if new_state.players[i].position > new_state.players[i_bet].position:
                        new_state.players[i].action = 'call'
                    else:
                        new_state.players[i].action = 'bet'
                        new_state.players[i_bet].action = 'call'

    def persist(self, stack):
        self.stack = self.states[0].stack
        self.reward = stack - self.stack
        self.hand = json.dumps(self.hand)
        self.save()
        for state in self.states:
            active_players=json.dumps([obj.to_dict() for obj in state.active_players()])
            game_state = GameState(
                code=self.code,
                hand=json.dumps(state.hand),
                board=json.dumps(state.board),
                position=state.position,
                stack=state.stack,
                pot=state.pot,
                stage=state.stage,
                strength=state.strength,
                win_rate=state.win_rate,
                call=state.call,
                action=state.action,
                players=active_players(),
                player1=json.dumps(state.players[0].to_dict()),
                player2=json.dumps(state.players[1].to_dict()),
                player3=json.dumps(state.players[2].to_dict()),
                player4=json.dumps(state.players[3].to_dict()),
                player5=json.dumps(state.players[4].to_dict()),
            )
            game_state.save()
        # self.state_data = json.dumps([obj.to_dict() for obj in self.states] if self.states else [])

    def to_dict(self):
        # states = []
        # for state in self.states:
        #     states.append({
        #         'stage': state.stage,
        #         'board': state.board,
        #         'pot': state.pot,
        #         'players': [player.to_dict() for player in state.players]
        #     })
        return {
            'hand': self.hand,
            'position': self.position,
            'states': self.states
        }


if __name__ == '__main__':
    db.connect()
    db.create_tables([Game, GameState])
