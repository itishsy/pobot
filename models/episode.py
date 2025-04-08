from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from game import State, Player


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
    player1_stack = FloatField(null=True)  #
    player1_amount = FloatField(null=True)  #
    player2_name = CharField(null=True)  # 玩家2
    player2_stack = FloatField(null=True)  #
    player2_amount = FloatField(null=True)  #
    player3_name = CharField(null=True)  # 玩家3
    player3_stack = FloatField(null=True)  #
    player3_amount = FloatField(null=True)  #
    player4_name = CharField(null=True)  # 玩家4
    player4_stack = FloatField(null=True)  #
    player4_amount = FloatField(null=True)  #
    player5_name = CharField(null=True)  # 玩家5
    player5_stack = FloatField(null=True)  #
    player5_amount = FloatField(null=True)  #

    def get_state(self):
        stage = 0
        board = []
        if self.card7:
            board = [self.card3, self.card4, self.card5, self.card6, self.card7]
            stage = 3
        elif self.card6:
            board = [self.card3, self.card4, self.card5, self.card6]
            stage = 2
        elif self.card5:
            board = [self.card3, self.card4, self.card5]
            stage = 1

        state = State(self.pool, stage, board)
        for i in range(1, 6):
            pos = (self.position + i) % 6 if self.position != 5 else 6
            name = eval('self.player{}_name'.format(i))
            stack = eval('self.player{}_amount'.format(i))
            state.players.append(Player(name, pos, stack))
