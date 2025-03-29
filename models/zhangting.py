from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField
from datetime import datetime


# HOT
class ZhangTing(BaseModel):
    class Meta:
        table_name = 'zhang_ting'

    date = CharField()  # 日期
    bk = CharField()  # 板块
    code = CharField()  # 票据
    name = CharField()  # 名称
    price = CharField()  # 题材
    zf = CharField()  # 涨幅
    ztt = CharField()  # 涨停时间
    comment = CharField()  # 解释
    source = CharField()  # 来源
    created = DateTimeField()

    @staticmethod
    def add(cod, nam, bk, price, zf, ztt, comment):
        cre = datetime.now().strftime("%Y-%m-%d")
        if not ZhangTing.select().where(ZhangTing.code == cod, ZhangTing.date == cre).exists():
            hot = ZhangTing()
            hot.date = cre
            hot.code = cod
            hot.name = nam
            hot.bk = bk
            hot.price = price
            hot.zf = zf
            hot.ztt = ztt
            hot.comment = comment
            hot.source = '韭研公社'
            hot.created = datetime.now()
            hot.save()


if __name__ == '__main__':
    db.connect()
    db.create_tables([ZhangTing])
