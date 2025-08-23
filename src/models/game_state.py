from config.db import BaseModel, JSONArrayField
from peewee import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime


class GameState(BaseModel):
    class Meta:
        table_name = 'game_state'

    id = AutoField()
    code = CharField()
    stage = IntegerField(null=True)
    position = IntegerField(null=True)
    stack = FloatField(null=True)
    hand = JSONArrayField()
    board = JSONArrayField(null=True)
    pot = FloatField(null=True)
    call = FloatField(null=True)
    player1 = TextField(null=True)
    player2 = TextField(null=True)
    player3 = TextField(null=True)
    player4 = TextField(null=True)
    player5 = TextField(null=True)

    features = CharField(null=True)

    strength = FloatField(null=True)
    win = FloatField(null=True)
    rwin = FloatField(null=True)
    ev = FloatField(null=True)
    ev_bet = FloatField(null=True)
    ev_action = IntegerField(null=True)

    action = IntegerField(null=True)
    reward = FloatField(null=True)

    pls = []

    def load_dict(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def get_player(self, name):
        for player in self.pls:
            if player.name == name:
                return player

    def actives(self):
        active_players = [p for p in self.pls if p.active == 1]
        return active_players

