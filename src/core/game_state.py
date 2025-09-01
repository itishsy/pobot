from re import A
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


"""
action type: fold,check,call,bet,raise,allin
action value: 0-fold,1-check/call,2-bet/raise/allin
"""

@dataclass
class Player:
    """Player information class"""
    id: str  # Player unique identifier
    name: str  # Player nickname
    position: int # Player position
    hand: List[str] # Player hole cards
    stack: int  # Player remaining chips
    is_in_hand: bool  # Whether player is still in the hand
    is_active: bool  # Whether player can act (not folded and not all-in)
    is_dealer: bool  # Whether player is the dealer
    is_small_blind: bool  # Whether player is small blind
    is_big_blind: bool  # Whether player is big blind
    bet_this_round: int # Player bet amount in current round
    bet_this_stage: int # Player bet amount in current stage
    bet_this_hand: int  # Total bet in this hand
    action: str # Player's action
    vpip: float = 0.0  # Player voluntary put money in pot rate statistics
    pfr: float = 0.0  # Player pre-flop raise rate statistics
    aggression_factor: float = 0.0  # Player aggression statistics
    three_bet_percent: float = 0.0  # Player 3Bet frequency statistics

@dataclass
class Round:
    """Game round class - records the board state before each player action round"""
    id: int # Timestamp
    stage: int  # Stage: 0: preflop, 1: flop, 2: turn, 3: river
    current_bet_round: int = 0  # Current betting round (multiple betting rounds possible within same stage)
    community_cards: List[str] = []  # Community cards
    pot: int = 0  # Current pot size
    call: int = 0  # Current call amount needed
    min_raise: int = 0  # Minimum raise amount
    max_raise: int = 0  # Maximum raise amount (usually player's remaining chips)

    current_player: Player # Current player
    active_opponents: List[Player] = []  # Current active players information


@dataclass
class GameState:
    """Game state class - records state information throughout a hand"""
    
    table_id: str = "" # Table ID
    big_blind: int = 0 # Big blind amount
    total_players: int = 6 # Number of seated players, 2-6 players
    player: Player = None # Current player
    opponents: List[Player] = [] # Other players information
    rounds: List[Round] = [] # All game states for current hand, including all information for each stage
    reward: int = 0 # Current player's reward

    def get_action_history(self) -> List[str]:
        """Get all action records for this hand"""
        action_history = []
        for round in self.rounds:
            action_history.extend(round.action_history)
        return action_history
    
    def get_current_street_actions(self) -> List[str]:
        """Get action records for current street"""
        current_street_actions = []
        for round in self.rounds:
            current_street_actions.extend(round.current_street_actions)
        return current_street_actions
    
    def get_preflop_raiser(self) -> Optional[str]:
        """Get the last preflop raiser"""
        for round in self.rounds:
            if round.stage == 0:
                return round.preflop_raiser
        return None
    
    def get_aggressor(self) -> Optional[str]:
        """Get the last aggressor in current round (bettor/raiser)"""
        for round in self.rounds:
            if round.stage == 0:
                return round.aggressor
        return None
    
    def get_last_raiser(self) -> Optional[str]:
        """Get the last raiser"""
        for round in self.rounds:
            if round.stage == 0:
                return round.last_raiser
        return None
