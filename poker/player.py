from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, DecimalField


class Player(BaseModel):
    id = AutoField()
    game_code = CharField()
    name = CharField()
    position = CharField()
    status = CharField()
    amount = DecimalField()  # 起始金额
    actions = []


class PlayerAction:
    player_id = IntegerField()
    stage = CharField()
    round = IntegerField()
    action = CharField()
    amount = DecimalField()

