from models.game_state import GameState

class GameFeature():

    def __init__(self, game_state: GameState) -> None:
        self.equity = 0
        self.wetness = 0
        self.strength = 0
        self.board = game_state.board
        self.hand = game_state.hand
        self.players = game_state.players
        self.pots = game_state.pots
        self.ppots = game_state.ppots
        self.calls = game_state.calls
        self.c_bet = game_state.c_bet
        self.c_bet_his = game_state.c_bet_his
        self.c_raise = game_state.c_raise
        self.c_raise_his = game_state.c_raise_his
        self.b_bet = game_state.b_bet
        self.b_bet_his = game_state.b_bet_his
        self.strength = game_state.strength
        self.wetness = game_state.wetness
        self.equity = game_state.equity

        