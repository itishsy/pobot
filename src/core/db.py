# -*- coding: utf-8 -*-

from peewee import MySQLDatabase, Model, TextField
import json
import os

# 192.168.0.113
# localhost
db = MySQLDatabase(host='192.168.0.113',
                   user='root',
                   passwd='root',
                   database='pobot')


class BaseModel(Model):
    class Meta:
        database = db

    def __str__(self):
        r = {}
        for k in self._data.keys():
            try:
                r[k] = str(getattr(self, k))
            except:
                r[k] = json.dumps(getattr(self, k))
        # return str(r)
        return json.dumps(r, ensure_ascii=False)


# 自定义JSON序列化字段
class JSONArrayField(TextField):
    def db_value(self, value):
        return json.dumps(value) if value else '[]'

    def python_value(self, value):
        return json.loads(value) if value else []


if __name__ == '__main__':
    from models.game import Game
    from models.game_state import GameState
    from models.hand_score import HandScore
    db.connect()
    db.create_tables([Game, GameState, HandScore])
