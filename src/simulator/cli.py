import random
from collections import defaultdict


from simulator.cal import distribute_pot
from core.game_state import GameState, Round, Player, Action, ActionType

class PokerGame:
    def __init__(self, player_names, small_blind=1, big_blind=2):
        self.players = [Player(name, 100) for name in player_names]
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.dealer_pos = 0
        self.pot = 0
        self.side_pots = []
        self.community_cards = []
        self.deck = self._create_deck()
        self.current_bet = 0
        self.round_name = "Pre-Flop"  # Pre-Flop, Flop, Turn, River
        self.stage_complete = False
        self.is_new_stage = True
        self.game_states = {}

    
    def _create_deck(self):
        ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        suits = ['♥','♦','♠','♣']
        return [rank + suit for suit in suits for rank in ranks]
    
    def shuffle_deck(self):
        random.shuffle(self.deck)
    
    def deal_hole_cards(self):
        for player in self.players:
            player.hand = [self.deck.pop(), self.deck.pop()]
    
    def post_blinds(self):
        sb_pos = (self.dealer_pos + 1) % len(self.players)
        bb_pos = (self.dealer_pos + 2) % len(self.players)
        
        sb_player = self.players[sb_pos]
        bb_player = self.players[bb_pos]
        
        # Collect small blind
        sb_amount = min(self.small_blind, sb_player.chips)
        sb_player.chips -= sb_amount
        sb_player.bet_this_round = sb_amount
        if sb_player.chips == 0:
            sb_player.all_in = True
        
        # Collect big blind
        bb_amount = min(self.big_blind, bb_player.chips)
        bb_player.chips -= bb_amount
        bb_player.bet_this_round = bb_amount
        if bb_player.chips == 0:
            bb_player.all_in = True
        
        # Update pot and current bet
        self.pot = sb_amount + bb_amount
        self.current_bet = bb_amount
    
    def get_active_players(self):
        return [p for p in self.players if not p.folded]
        # return [p for p in self.players if not p.folded and not p.all_in]
    
    def betting_round_complete(self):
        active_players = self.get_active_players()
        if not active_players:
            return True
        if self.is_new_stage:
            self.is_new_stage = False
            return False
        # All active players have matched the current bet or are all-in
        for player in active_players:
            if player.bet_this_round < self.current_bet:
                return False
        return True
    
    def reset_for_new_stage(self):
        # Reset betting state, don't collect pot (already collected at end of betting_round)
        self.current_bet = 0
        self.is_new_stage = True

        for player in self.players:
            player.bet_this_round = 0
            player.action = None
        self.stage_complete = False
    
    def deal_community_cards(self, num_cards):
        if len(self.deck) < num_cards:
            return False
        
        new_cards = [self.deck.pop() for _ in range(num_cards)]
        self.community_cards.extend(new_cards)
        
        if len(self.community_cards) == 3:
            self.round_name = "Flop"
        elif len(self.community_cards) == 4:
            self.round_name = "Turn"
        elif len(self.community_cards) == 5:
            self.round_name = "River"
        
        return True
    
    def get_valid_actions(self, player):
        actions = []
        call_amount = self.current_bet - player.bet_this_round
        
        if call_amount == 0:
            actions.append(0)  # Check
        else:
            actions.append(1)  # Call
        
        if player.chips > call_amount:
            actions.append(2)  # Raise
        
        # Fold is always allowed (represented as 0), but only add if not already present
        if 0 not in actions:
            actions.append(0)  # Fold
        return actions
    
    def process_player_action(self, player, action, raise_amount=0):
        call_amount = self.current_bet - player.bet_this_round
        
        if action == 0:  # Fold/Check
            if call_amount > 0:
                player.folded = True
                player.action = 'Fold'
                print(f"{player.name} folds")
            else:
                player.action = 'Check'
                print(f"{player.name} checks")
        
        elif action == 1:  # Call
            actual_call = min(call_amount, player.chips)
            player.chips -= actual_call
            player.bet_this_round += actual_call
            player.total_bet += actual_call  # Update total bet
            
            # Update pot immediately
            self.pot += actual_call
            
            if player.chips == 0:
                player.all_in = True
                player.action = 'Call'
                print(f"{player.name} calls ${actual_call} and is all-in!")
            else:
                player.action = 'Call'
                print(f"{player.name} calls ${actual_call}")
        
        elif action == 2:  # Raise
            min_raise = max(self.big_blind, self.current_bet - player.bet_this_round)
            
            # Validate raise amount
            if raise_amount < min_raise:
                print(f"❌ Error: Raise amount ${raise_amount} is less than minimum raise ${min_raise}")
                return
            
            # Ensure raise amount is at least minimum raise
            raise_amount = max(raise_amount, min_raise)
            total_needed = call_amount + raise_amount
            
            if total_needed > player.chips:
                total_needed = player.chips
                raise_amount = total_needed - call_amount
            
            player.chips -= total_needed
            player.bet_this_round += total_needed
            player.total_bet += total_needed  # Update total bet
            
            # Update pot immediately
            self.pot += total_needed
            self.current_bet = player.bet_this_round
            
            if player.chips == 0:
                player.all_in = True
                player.action = 'Raise'
                print(f"{player.name} raises ${raise_amount} (all-in)! New bet: ${self.current_bet}")
            else:
                player.action = 'Raise'
                print(f"{player.name} raises ${raise_amount}. New bet: ${self.current_bet}")
    
    def collect_bets(self):
        # Pot already updated in real-time when players bet, just reset betting state here
        for player in self.players:
            player.bet_this_round = 0
    
    def print_game_state(self):
        print(f"\n--- {self.round_name} ---")
        print(f"Pot: {self.pot} | Current bet: {self.current_bet}")
        print(f"Community cards: {' '.join(self.community_cards) if self.community_cards else 'None'}")
        print()
        # Only print non-folded players
        active_players_count = 0
        for i, player in enumerate(self.players):
            if player.folded:
                continue  # Skip folded players
            
            status = ""
            if player.all_in:
                status = " (All-in)"

            sb_pos = (self.dealer_pos + 1) % len(self.players)
            bb_pos = (self.dealer_pos + 2) % len(self.players)
            position = []
            if i == self.dealer_pos:
                position.append("[Dealer]")
            if i == sb_pos:
                position.append("[SB]")
            if i == bb_pos:
                position.append("[BB]")
            position_str = ' '.join(position)
            action_log = f' [{player.action}]' if hasattr(player, 'action') else ''
            print(f"{i}: {player.name} {position_str} - {player.chips}{status}{action_log}")
            active_players_count += 1
    
    def play_round(self):

        for player in self.players:
            game_state = GameState()
            game_state.table_id = "simulator_table"
            game_state.big_blind = self.big_blind
            game_state.total_players = len(self.players)
            game_state.current_player = player
            game_state.opponents = [player for player in self.players if player != game_state.current_player]
            game_state.rounds = []
            game_state.reward = 0
            game_state.rounds.append(Round(stage=0, current_bet_round=0, community_cards=[], pot=0, call=0, min_raise=0, max_raise=0, opponents=[player for player in self.players if player != game_state.current_player]))
            self.game_states[player.name] = game_state

        # Pre-Flop
        self.deal_hole_cards()
        self.post_blinds()
        self.betting_round()

        # Flop
        if len(self.get_active_players()) >= 2:
            self.reset_for_new_stage()
            self.deal_community_cards(3)
            self.betting_round()

        # Turn
        if len(self.get_active_players()) >= 2:
            self.reset_for_new_stage()
            self.deal_community_cards(1)
            self.betting_round()
        
        # River
        if len(self.get_active_players()) >= 2:
            self.reset_for_new_stage()
            self.deal_community_cards(1)
            self.betting_round()
        
        # Showdown
        distribute_pot(self.get_active_players(), self.community_cards, self.pot)

        # Prepare for next hand
        self.community_cards = []
        self.dealer_pos = (self.dealer_pos + 1) % len(self.players)
        for player in self.players:
            player.folded = False
            player.all_in = False
            player.bet_this_round = 0
            player.total_bet = 0  # Reset total bet for next hand
            player.hand = []
        
        self.deck = self._create_deck()
        self.shuffle_deck()
        self.pot = 0
        self.current_bet = 0
        self.round_name = "Pre-Flop"
    
    def betting_round(self):
        if self.round_name == "Pre-Flop":
            start_pos = (self.dealer_pos + 3) % len(self.players)  # UTG position   
        else:
            start_pos = (self.dealer_pos + 1) % len(self.players)  # SB position
        
        last_raiser = None
        first_to_act = True
        
        while not self.betting_round_complete():
            for i in range(len(self.players)):
                player_idx = (start_pos + i) % len(self.players)
                player = self.players[player_idx]
                
                if player.folded or player.all_in:
                    continue
                
                if not first_to_act and player_idx == last_raiser:
                    self.stage_complete = True
                    break
                
                self.print_game_state()
                print(f"\n{player.name}'s turn (Cards: {' '.join(player.hand)})")
                
                valid_actions = self.get_valid_actions(player)
                
                # Dynamically display action options based on available actions
                action_descriptions = []
                for action in valid_actions:
                    if action == 0:
                        if self.current_bet == 0:
                            action_descriptions.append("0-Check")
                        else:
                            action_descriptions.append("0-Fold")
                    elif action == 1:
                        action_descriptions.append("1-Call")
                    elif action == 2:
                        action_descriptions.append("2-Raise")
                
                print(f"Actions: {' | '.join(action_descriptions)}")

                while True:
                    try:
                        action = int(input("Choose action: "))
                        if action not in valid_actions:
                            if action == -1:
                                print("Quitting game...")
                                exit()

                            print("Invalid action. Try again.")
                            continue
                        
                        raise_amt = 0
                        if action == 2:
                            min_raise = max(self.big_blind, self.current_bet * 2 - player.bet_this_round)
                            max_raise = player.chips + player.bet_this_round - self.current_bet
                            raise_amt = int(input(f"Raise amount (${min_raise}-${max_raise}): "))
                            if raise_amt < min_raise or raise_amt > max_raise:
                                print(f"Invalid raise amount. Must be between ${min_raise} and ${max_raise}")
                                continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                
                self.process_player_action(player, action, raise_amt)
                round = Round(stage=0, current_bet_round=0, community_cards=[], pot=0, call=0, min_raise=0, max_raise=0, opponents=[player for player in self.players if player != game_state.current_player])
                round.action = Action(action_type=ActionType.RAISE, amount=raise_amt)
                self.game_states[player.name].rounds.append(round)
                
                if action == 2:  # Raise
                    last_raiser = player_idx
                
                if len(self.get_active_players()) <= 1:
                    self.stage_complete = True
                    break
            
            first_to_act = False
        
        # Collect pot at the end of each betting round
        if self.round_name == "Pre-Flop":
            # Collect pot at end of Preflop stage
            self.collect_bets()
        else:
            # Collect pot at end of other stages
            self.collect_bets()

def main():
    print("Texas Hold'em Poker - 6 Player Game")
    player_names = ["Alex", "Ben", "Chloe", "Daniel", "Evelyn", "Felix"]

    game = PokerGame(player_names)
    
    for i in range(3):  # Play 3 hands
        print(f"\n=== Hand #{i+1} ===")
        game.shuffle_deck()
        game.play_round()
        
        # Remove players with no chips
        game.players = [p for p in game.players if p.chips > 0]
        if len(game.players) < 2:
            print("Game over - only one player remains!")
            print(game.players[0].name, game.players[0].chips)
            break

if __name__ == "__main__":
    main()