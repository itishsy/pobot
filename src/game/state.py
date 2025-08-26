from typing import List, Dict, Optional

from game.action import Action
from game.player import Player

class GameState:
    def __init__(self):

        # board related
        self.community_cards = []
        self.pot: int = 0
        self.current_bet: int = 0

        # player related
        self.my_hand = []
        self.my_stack: int = 0
        self.my_position: int = 0

        # history
        self.opponents: Dict[Player] = {}
        self.history: List[Action] = []
        self.dealer_button_pos: int = 0
