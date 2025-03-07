from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
import json

from poker.models.hand_score import HandScore
from poker.card import order_cards


class Player:
    def __init__(self, name, position, stack):
        self.name = name
        self.position = position
        self.stack = stack
        self.action = None
        self.amount = None
        self.active = True

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
    def __init__(self, section):
        self.pot = section.pool
        self.stage = section.get_state()
        self.players = []
        self.board = []

        if self.stage == 'flop':
            self.board = [self.card3, self.card4, self.card5]
        elif self.stage == 'turn':
            self.board = [self.card3, self.card4, self.card5, self.card6]
        elif self.stage == 'river':
            self.board = [self.card3, self.card4, self.card5, self.card6, self.card7]

        for i in range(1, 6):
            player_name = eval('section.player{}_name'.format(i))
            player_amount = eval('section.player{}_amount'.format(i))
            player_position = eval('section.player{}_position'.format(i))
            self.players.append(Player(player_name, player_position, player_amount))
            

    def to_dict(self):
        return {
            'stage': self.stage,
            'board': self.board,
            'pot': self.pot,
            'players': self.players
        }
        
    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.stage = data['stage']
        obj.board = data['board']
        obj.pot = data['pot']
        obj.players = data['players']
        return obj

class Game(BaseModel):
    class Meta:
        table_name = 'game_episode'

    id = AutoField()
    code = CharField()
    hand = CharField()
    position = IntegerField()
    stack = FloatField()
    reward = FloatField()
    state_data = TextField()  # 实际存储的JSON数据
    
    @property
    def states(self):
        """反序列化存储的JSON数据为State对象集合"""
        return [State.from_dict(d) for d in json.loads(self.state_data or '[]')]
    
    @states.setter
    def states(self, value):
        """序列化State对象集合为JSON存储"""
        self.state_data = json.dumps([obj.to_dict() for obj in value] if value else [])
    

    def __init__(self, section, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code = datetime.now().strftime('%Y%m%d%H%M%S')
        self.hand = order_cards(section.card1, section.card2)
        self.position = section.position
        self.stage = section.stage
        self.states = [State(section)] 
        self.created = datetime.now()

    def update_players_status(self):
        """根据最新section更新所有state中玩家的动作"""
        # 获取当前状态副本
        updated_states = [s for s in self.states]
        
        # 只更新最新state的玩家动作
        if updated_states:
            state_size = len(updated_states)
            if state_size == 1:
                player_size = len(updated_states[0].players)
                for i in range(1, 6):
                    """1-5"""
                    player_position = (self.position + i) % 6
                    player_position = 6 if player_position == 0 else player_position
                    player = updated_states[0].players[i-1]
                    name = player['name']
                    stack = player['stack']
                    if name:
                        player['position'] = player_position
                        player['action'] = None
            else:
                for i in range(size - 1):
                    state = updated_states[i]
                    for player in state.players:
                        player['action'] = None

        # 更新状态列表
        self.states = updated_states

    def to_dict(self):
        states = []
        for state in self.states:
            state_dict = state.to_dict()
            state_dict['players'] = [player.to_dict() for player in state.players]
            states.append(state_dict)
        return {
            'hand': self.hand,
            'position': self.position,
            'states': states
        }