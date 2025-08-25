from config.db import BaseModel, JSONArrayField
from peewee import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime


class GameState(BaseModel):
    class Meta:
        table_name = 'game_state'

    id = AutoField()
    code = CharField()  # 游戏代码, game类实例的code,每一局游戏一个代码，一局游戏有多个state
    stage = IntegerField(null=True)  # 阶段 0: preflop, 1: flop, 2: turn, 3: river
    round = IntegerField(null=True)  # 轮次 每一stage有多个round,

    # 当前玩家信息
    name = CharField(null=True)  # 玩家名称
    hand = JSONArrayField()  # 当前操作玩家的手牌
    position = IntegerField(null=True)  # 当前操作玩家的位置
    stack = FloatField(null=True)  # 当前操作玩家剩余的筹码

    # 牌面信息
    community_cards = JSONArrayField(null=True)  # 公共牌
    pot = FloatField(null=True)  # 底池
    call = FloatField(null=True)  # 需要跟注的筹码

    # 其他玩家信息，GamePlayer类实例json化后存储. 用于计算当前操作玩家的手牌强度
    player1 = TextField(null=True)  # 位于当前操作玩家的下1位玩家
    player2 = TextField(null=True)  # 位于当前操作玩家的下2位玩家
    player3 = TextField(null=True)  # 位于当前操作玩家的下3位玩家
    player4 = TextField(null=True)  # 位于当前操作玩家的下4位玩家
    player5 = TextField(null=True)  # 位于当前操作玩家的下5位玩家
    strength = FloatField(null=True)  # 当前操作玩家的手牌强度， 调用game_feature.py中的eval_strength函数计算
    
    win = FloatField(null=True)  # 当前操作玩家赢的概率
    rwin = FloatField(null=True)  # 当前操作玩家赢的概率
    ev = FloatField(null=True)  # 当前操作玩家赢的概率
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

    def print_basic_state(self):
        """打印基本信息"""
        print(f"code: {self.code}, stage: {self.stage}, round: {self.round}, name: {self.name}, hand: {self.hand}, position: {self.position}, stack: {self.stack}, community_cards: {self.community_cards}, pot: {self.pot}, call: {self.call}, player1: {self.player1}, player2: {self.player2}, player3: {self.player3}, player4: {self.player4}, player5: {self.player5}, strength: {self.strength}")
