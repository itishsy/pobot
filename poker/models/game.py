from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
import json
import copy
from poker.config import SB, BB
from decimal import Decimal
from poker.models.hand_score import HandScore
from poker.card import order_cards


class GameState(BaseModel):
    class Meta:
        table_name = 'game_state'

    id = AutoField()
    code = CharField()
    hand = CharField()
    board = CharField(null=True)
    position = IntegerField(null=True)
    stack = FloatField(null=True)
    pot = FloatField(null=True)
    stage = IntegerField(null=True)
    call = FloatField(null=True)
    action = CharField(null=True)
    player1 = TextField(null=True)
    player2 = TextField(null=True)
    player3 = TextField(null=True)
    player4 = TextField(null=True)
    player5 = TextField(null=True)


class Player:
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
    reward = None
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
            print('new game')
            if self.hand is not None:
                self.persist(state.stack)
                self.states.clear()
            self.code = datetime.now().strftime('%Y%m%d%H%M%S')
            self.hand = state.hand
            self.position = state.position
            self.stack = state.stack
            first_state = copy.deepcopy(state)
            first_state.code = self.code
            first_state.pot = SB + BB
            first_state.players.clear()
            for i in range(1, 6):
                player = state.players[i-1]
                player.stack = player.stack + player.amount
                first_state.players.append(player)
            self.states.append(first_state)

        # sle = len(self.states)
        pre_state = self.states[-1]
        if state.stage != pre_state.stage or state.pot != pre_state.pot:
            # 计算玩家action, 追加最新state
            state.code = self.code
            self.set_players_state(state)
            self.states.append(state)
        # print('states1:{}'.format(sle), 'states2:{}'.format(len(self.states)))


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
            game_state = GameState(
                code=self.code,
                hand=json.dumps(state.hand),
                board=json.dumps(state.board),
                position=state.position,
                stack=state.stack,
                pot=state.pot,
                stage=state.stage,
                call=state.call,
                action=state.action,
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
