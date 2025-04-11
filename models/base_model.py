# -*- coding: utf-8 -*-

from flask_peewee.db import MySQLDatabase, Model
import json
import os


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


if __name__ == '__main__':
    from models.game import Game, GameState
    from models.card import HandScore

    db.connect()
    db.create_tables([Game, State, HandScore])
