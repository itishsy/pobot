from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
import json
import copy
from poker.config import SB, BB
from decimal import Decimal
from poker.models.hand_score import HandScore
from poker.card import order_cards


class Player:
    def __init__(self, name, position, stack, action='pending', amount=None):
        self.name = name
        self.position = position
        self.stack = stack
        self.action = action
        self.amount = amount
        self.active = True if name else False

    def to_dict(self):
        return {
            'name': self.name,
            'position': self.position,
            'stack': self.stack,
            'action': self.action,
            'amount': self.amount,
            'active': self.active
        }


class State(BaseModel):
    code = CharField()
    hand = CharField()
    position = IntegerField()

    board = CharField()
    pot = FloatField()
    stage = IntegerField()
    players_data = TextField()

    action = IntegerField()
    reward = FloatField()
    players = []

    @staticmethod
    def from_dict(data):
        obj = State()
        obj.pot = data['pot']
        obj.stage = data['stage']
        obj.board = data['board']
        obj.players = data['players']
        obj.players_data = json.dumps([obj.to_dict() for obj in obj.players] if obj.players else [])
        return obj

    def to_dict(self):
        return {
            'stage': self.stage,
            'board': self.board,
            'pot': self.pot,
            'players': self.players,
            'action': self.action,
            'reward': self.reward
        }


class Game(BaseModel):
    class Meta:
        table_name = 'game'

    id = AutoField()
    code = CharField()
    hand = CharField()
    position = IntegerField()
    stack = FloatField()
    reward = FloatField()
    state_data = TextField()  # 实际存储的JSON数据

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
            if self.hand is not None:
                self.save()
                self.states.clear()
            self.code = datetime.now().strftime('%Y%m%d%H%M%S')
            self.hand = state.hand
            self.position = state.position
            first_state = copy.deepcopy(state)
            first_state.code = self.code
            first_state.pot = SB + BB
            for i in range(1, 6):
                player = first_state.players[i-1]
                player.stack = player.stack + player.amount
                first_state.players.append(player)
            self.states.append(first_state)

        pre_state = self.states[-1]
        if state.stage != pre_state.stage or state.pot != pre_state.pot:
            # 计算玩家action, 追加最新state
            state.code = self.code
            self.set_players_action(state, pre_state)
            self.states.append(state)
            self.state_data = json.dumps([obj.to_dict() for obj in self.states] if self.states else [])

    @staticmethod
    def set_players_action(state, pre_state):
        dif_pot = state.pot - pre_state.pot
        i_bet = -1
        i_bet_amount = 0.0
        for i in range(5):
            if pre_state.players[i].action == 'fold':
                state.players[i].action = 'fold'
                continue

            dif_stack = pre_state.players[i].stack - state.players[i].stack
            if dif_pot > 0 and dif_stack == 0:
                # 底池增加，玩家码量无变化
                state.players[i].action = 'fold'
                continue

            if dif_pot == 0:
                state.players[i].action = 'check'
                continue

            if dif_pot == dif_stack:
                # 底池与玩家码量变化相等，一家下注
                state.players[i].action = 'bet'
                state.players[i].amount = dif_stack
                continue

            # 底池大于玩家码量变化。能整除，说明前bet+后call，不能整除，说明前bet+后raise. 会存在误差，先忽略
            if i_bet < 0:
                i_bet = i
                i_bet_amount = dif_stack
                state.players[i].action = 'bet'
                state.players[i].amount = dif_stack
            else:
                if dif_stack > i_bet_amount:
                    i_bet = i
                    i_bet_amount = dif_stack
                    state.players[i].action = 'raise'
                    state.players[i].amount = dif_stack
                elif dif_stack < i_bet_amount:
                    state.players[i].action = 'bet'
                    state.players[i].amount = dif_stack
                    state.players[i_bet].action = 'raise'
                else:
                    if state.players[i].position > state.players[i_bet].position:
                        state.players[i].action = 'call'
                    else:
                        state.players[i].action = 'bet'
                        state.players[i_bet].action = 'call'

    def to_dict(self):
        states = []
        for state in self.states:
            states.append({
                'stage': state.stage,
                'board': state.board,
                'pot': state.pot,
                'players': [player.to_dict() for player in state.players]
            })
        return {
            'hand': self.hand,
            'position': self.position,
            'states': states
        }
