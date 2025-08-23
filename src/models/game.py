from config.db import BaseModel, JSONArrayField
from config.gg import SB, BB
from peewee import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
from .game_state import GameState
from .game_player import Player



class Game(BaseModel):
    class Meta:
        table_name = 'game'

    id = AutoField()
    code = CharField()
    bb = FloatField()
    hand = JSONArrayField()
    position = IntegerField(null=True)
    stack = FloatField(null=True)
    reward = FloatField(null=True)

    states = []

    def new(self, state):
        self.code = datetime.now().strftime('%Y%m%d%H%M%S')
        self.bb = 0.02
        self.hand = state.hand
        self.position = state.position
        self.stack = state.stack

        self.states.clear()
        sta = GameState()
        sta.code = self.code
        sta.hand = state.hand
        sta.position = state.position
        sta.stage = 0
        sta.pot = 0.0
        sta.call = 0.0
        sta.board = None
        sta.players = 1
        if state.position == 0:
            sta.stack = round(state.stack + SB, 2)
        elif state.position == 1:
            sta.stack = round(state.stack + BB, 2)
        else:
            sta.stack = state.stack
        sta.pls = []

        for sp in state.pls:
            if sp.position == 0:
                stack = round(sp.stack + SB, 2)
            elif sp.position == 1:
                stack = round(sp.stack + BB, 2)
            else:
                stack = round(sp.stack + sp.amount, 2)
            if sp.name is not None and sp.name != '' and sp.stack > 0:
                sta.players = sta.players + 1
            sta.pls.append(Player(sp.name, sp.position, stack, action='', active=True))
        self.states = [sta]

    def add_state(self, state, persist=True):
        if state.hand != self.hand or state.position != self.position:
            print('------------------new game:', state.stack, state.hand, ' ------------------')
            self.new(state)
        pre_state = self.states[-1]
        if state.stage != pre_state.stage or state.pot != pre_state.pot:
            # 刷新玩家的action
            state.code = self.code
            for i in range(5):
                cur_player = state.pls[i]
                if cur_player.active:
                    pre_player = pre_state.pls[i]
                    if pre_player.action == 'pending':
                        gp = pre_state.get_player(pre_player.name)
                        if gp:
                            pre_player.action = 'call'
                        else:
                            pre_player.action = 'fold'
                    if pre_player.stack > cur_player.stack:
                        dif_amt = pre_player.stack - cur_player.stack
                        dif_pot = state.pot - pre_state.pot
                        cur_player.amount = dif_amt
                        cur_player.action = 'bet' if dif_pot == dif_amt else 'raise'
            self.states.append(state)
            return True
        return False

    def persist(self, save_all=False):
        state = self.states[-1]
        self.reward = state.stack - self.stack
        if Game.select().where(Game.code == self.code).exists():
            Game.update(reward=self.reward).where(Game.code == self.code).execute()
        else:
            self.save()
        if save_all:
            GameState.delete().where(GameState.code == self.code).execute()
            for i in range(1, len(self.states)):
                sta = self.states[i]
                sta.reward = sta.pot if self.reward > 0 else self.reward
                sta.player1 = sta.pls[0].to_dict()
                sta.player2 = sta.pls[1].to_dict()
                sta.player3 = sta.pls[2].to_dict()
                sta.player4 = sta.pls[3].to_dict()
                sta.player5 = sta.pls[4].to_dict()
                sta.features = sta.feature.to_dict()
                sta.save()
        else:
            state.reward = state.pot if self.reward > 0 else self.reward
            state.player1 = state.pls[0].to_dict()
            state.player2 = state.pls[1].to_dict()
            state.player3 = state.pls[2].to_dict()
            state.player4 = state.pls[3].to_dict()
            state.player5 = state.pls[4].to_dict()
            state.features = state.feature.to_dict()
            state.save()

