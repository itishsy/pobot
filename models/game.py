from models.base_model import BaseModel, db, JSONArrayField
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, FloatField, TextField
from datetime import datetime
import copy
from config import SB, BB


class GameState(BaseModel):
    class Meta:
        table_name = 'game_state'

    id = AutoField()
    code = CharField()
    hand = JSONArrayField()
    position = IntegerField(null=True)
    stage = IntegerField(null=True)
    stack = FloatField(null=True)
    pot = FloatField(null=True)
    board = JSONArrayField(null=True)
    call = FloatField(null=True)
    action = CharField(null=True)
    amount = FloatField(null=True)
    strength = CharField(null=True)
    win_rate = FloatField(null=True)
    call_ev = FloatField(null=True)
    raise_ev = FloatField(null=True)
    bet_ev = FloatField(null=True)
    players = JSONArrayField(null=True)
    player1 = TextField(null=True)
    player2 = TextField(null=True)
    player3 = TextField(null=True)
    player4 = TextField(null=True)
    player5 = TextField(null=True)
    reward = FloatField(null=True)

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player

    def to_dict(self):
        pls = []
        for p in self.players:
            pls.append(p.to_dict())
        return {
            'code': self.code,
            'hand': self.hand,
            'position': self.position,
            'stage': self.stage,
            'stack': self.stack,
            'pot': self.pot,
            'board': self.board,
            'call': self.call,
            'action': self.action,
            'amount': self.amount,
            'strength': self.strength,
            'win_rate': self.win_rate,
            'call_ev': self.call_ev,
            'raise_ev': self.raise_ev,
            'bet_ev': self.bet_ev,
            'players': pls
        }

    def active_players(self):
        active_players = [p for p in self.players if p.active == 1]
        return sorted(active_players, key=lambda x: x.position)


class Player:
    name = None
    position = None
    stack = 0.0
    action = None
    amount = 0.0
    active = None

    def __init__(self, name, position, stack, action='pending', active=None, amount=None):
        self.name = name
        self.position = position
        self.stack = stack
        self.action = action
        self.amount = amount
        if active is None:
            self.active = True if name else False
        else:
            self.active = active

    def to_dict(self):
        return {
            'name': self.name,
            'position': self.position,
            'stack': self.stack,
            'action': self.action,
            'amount': self.amount,
            'active': self.active
        }


class Game(BaseModel):
    class Meta:
        table_name = 'game'

    id = AutoField()
    code = CharField()
    hand = JSONArrayField()
    position = IntegerField(null=True)
    stack = FloatField(null=True)
    reward = FloatField(null=True)

    states = []
    opponent_ranges = []

    def add_state(self, ocr_state):
        if ocr_state.hand != self.hand or ocr_state.position != self.position:
            print('------------------new game:', ocr_state.stack, ' ------------------')
            if self.hand is not None:
                self.persist(ocr_state.stack)
            self.states.clear()
            self.opponent_ranges.clear()
            self.code = datetime.now().strftime('%Y%m%d%H%M%S')
            self.hand = ocr_state.hand
            self.position = ocr_state.position
            self.stack = ocr_state.stack
            state0 = copy.deepcopy(ocr_state)
            state0.code = self.code
            state0.stage = 0
            state0.pot = SB + BB
            state0.players.clear()
            for sp in ocr_state.players:
                if sp.position == 0:
                    action = 'sb'
                    stack = round(sp.stack + SB, 2)
                elif sp.position == 1:
                    action = 'bb'
                    stack = round(sp.stack + BB, 2)
                else:
                    action = 'pending'
                    stack = round(sp.stack + sp.amount, 2)
                state0.players.append(Player(sp.name, sp.position, stack, action=action, active=True))
            self.states.append(state0)

        last_state = self.states[-1]
        if ocr_state.stage != last_state.stage or ocr_state.pot != last_state.pot:
            # 计算玩家action, 追加最新state
            ocr_state.code = self.code
            for lp in last_state.players:
                if lp.action == 'pending':
                    gp = last_state.get_player(lp.name)
                    if gp:
                        lp.action = 'call'
                    else:
                        lp.action = 'fold'
            active_players = []
            for sp in ocr_state.players:
                if sp.active == 1:
                    active_players.append(sp)
            ocr_state.players = active_players
            self.states.append(ocr_state)

    def persist(self, stack):
        self.stack = self.states[0].stack
        self.reward = stack - self.stack
        self.save()
        for state in self.states:
            if self.reward > 0:
                state.reward = state.pot
            else:
                state.reward = self.reward
            # active_players=json.dumps([obj.to_dict() for obj in state.active_players()])
            # game_state = GameState(
            #     code=self.code,
            #     hand=json.dumps(state.hand),
            #     board=json.dumps(state.board),
            #     position=state.position,
            #     stack=state.stack,
            #     pot=state.pot,
            #     stage=state.stage,
            #     strength=state.strength,
            #     win_rate=state.win_rate,
            #     call=state.call,
            #     action=state.action,
            #     players=active_players(),
            #     player1=json.dumps(state.players[0].to_dict()),
            #     player2=json.dumps(state.players[1].to_dict()),
            #     player3=json.dumps(state.players[2].to_dict()),
            #     player4=json.dumps(state.players[3].to_dict()),
            #     player5=json.dumps(state.players[4].to_dict()),
            # )
            state.save()
        # self.state_data = json.dumps([obj.to_dict() for obj in self.states] if self.states else [])

    def to_dict(self):
        # states = []
        # for state in self.states:
        #     states.append({
        #         'stage': state.stage,
        #         'board': state.board,
        #         'pot': state.pot,
        #         'players': [player.to_dict() for player in state.players]
        #     })
        return {
            'hand': self.hand,
            'position': self.position,
            'states': self.states
        }


if __name__ == '__main__':
    db.connect()
    db.create_tables([Game, GameState])
