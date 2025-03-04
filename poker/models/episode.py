from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField
from datetime import datetime


class Episode(BaseModel):
    code = CharField()
    hand = CharField()
    position = IntegerField()
    stack = FloatField()
    reward = FloatField()
    states = CharField()


class State:

    def __init__(self, stage, board, pot):
        self.stage = stage
        self.board = board
        self.pot = pot
        self.players = []

    def add_player(self, name, pos, stack):
        self.players.append({
            'id': name,
            'pos': pos,
            'stack': stack,
            'active': None,
            'action': None
        })

    def get(self):
        return {
            'stage': self.stage,
            'board': self.board,
            'pot': self.pot,
            'players': self.players
        }

