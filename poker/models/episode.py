
from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField


# 牌桌信息
class Section(BaseModel):
    class Meta:
        table_name = 'game_section'

    """
    每次需要做决策时，根据捕获的tableImage生成一个section
    """
    id = AutoField()
    game_code = CharField()
    pool = FloatField()  # 底池
    position = IntegerField()  # 座位
    balance = FloatField()  # 余额
    card1 = CharField()  # 手牌1
    card2 = CharField()  # 手牌2
    card3 = CharField(null=True)  # 公共牌1
    card4 = CharField(null=True)  # 公共牌2
    card5 = CharField(null=True)  # 公共牌3
    card6 = CharField(null=True)  # 公共牌4
    card7 = CharField(null=True)  # 公共牌5
    call_txt = CharField(null=True)  # 跟注金额ocr内容
    call = FloatField(null=True)  # 跟注金额

    player1_name = CharField(null=True)  # 玩家1
    player1_amount = FloatField(null=True)  #
    player2_name = CharField(null=True)  # 玩家2
    player2_amount = FloatField(null=True)  #
    player3_name = CharField(null=True)  # 玩家3
    player3_amount = FloatField(null=True)  #
    player4_name = CharField(null=True)  # 玩家4
    player4_amount = FloatField(null=True)  #
    player5_name = CharField(null=True)  # 玩家5
    player5_amount = FloatField(null=True)  #



