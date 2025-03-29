from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField
from datetime import datetime


# HOT
class Hot(BaseModel):
    date = CharField()  # 日期
    code = CharField()  # 票据
    name = CharField()  # 名称
    source = CharField()  # 来源
    rank = IntegerField()  # 排名
    created = DateTimeField()

    @staticmethod
    def add(cod, nam, sou, ran):
        cre = datetime.now().strftime("%Y-%m-%d")
        if not Hot.select().where(Hot.code == cod, Hot.source == sou, Hot.created == cre).exists():
            hot = Hot()
            hot.date = cre
            hot.code = cod
            hot.name = nam
            hot.source = sou
            hot.rank = ran
            hot.created = datetime.now()
            hot.save()


if __name__ == '__main__':
    db.connect()
    db.create_tables([Hot])
