import random
from collections import defaultdict
try:
    from .cal import distribute_pot
except ImportError:
    from cal import distribute_pot


class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.hand = []
        self.folded = False
        self.all_in = False
        self.bet_this_round = 0
        self.total_bet = 0  # Total bet in this hand
        self.action = None
        self.position = 0  # Player position
    
    def __str__(self):
        return f"{self.name} (${self.chips})"
    
    def calculate_hand_strength(self, community_cards):
        """Calculate hand strength (0-100)"""
        if not self.hand or len(self.hand) < 2:
            return 0
        
        # Use more complex hand strength calculation
        hand_value = 0
        
        # Basic rank calculation
        for card in self.hand:
            rank = card[:-1]
            if rank == 'A':
                hand_value += 14
            elif rank == 'K':
                hand_value += 13
            elif rank == 'Q':
                hand_value += 12
            elif rank == 'J':
                hand_value += 11
            elif rank == '10':
                hand_value += 10
            else:
                hand_value += int(rank)
        
        # Suited bonus
        if len(self.hand) == 2 and self.hand[0][-1] == self.hand[1][-1]:
            hand_value += 10
        
        # Pair bonus
        if len(self.hand) == 2 and self.hand[0][:-1] == self.hand[1][:-1]:
            hand_value += 20
        
        # Connected cards bonus
        if len(self.hand) == 2:
            rank1 = self.hand[0][:-1]
            rank2 = self.hand[1][:-1]
            if rank1 == 'A' and rank2 in ['K', 'Q']:
                hand_value += 15
            elif rank1 == 'K' and rank2 == 'Q':
                hand_value += 12
            elif rank1 == 'Q' and rank2 == 'J':
                hand_value += 10
        
        # Normalize to 0-100 range
        return min(hand_value * 2, 100)
    
    def get_standard_features(self, game_state):
        """Generate standard GameFeature features"""
        features = {}
        
        # 1. Stage (0: preflop, 1: flop, 2: turn, 3: river)
        stage_map = {"Pre-Flop": 0, "Flop": 1, "Turn": 2, "River": 3}
        features['stage'] = stage_map.get(game_state['round_name'], 0)
        
        # 2. Position (0: early, 1: middle, 2: late)
        relative_pos = (game_state['player_index'] - game_state['dealer_pos']) % game_state['total_players']
        if relative_pos <= 1:
            features['pos'] = 0  # Early position
        elif relative_pos >= game_state['total_players'] - 2:
            features['pos'] = 2  # Late position
        else:
            features['pos'] = 1  # Middle position
        
        # 3. Pot size (BB)
        features['pots'] = round(game_state['pot'] / game_state['big_blind'], 2)
        
        # 4. Preflop pot size (BB)
        if game_state['round_name'] == "Pre-Flop":
            features['ppots'] = features['pots']
        else:
            # Simplified handling, should record preflop pot
            features['ppots'] = round(3 / game_state['big_blind'], 2)  # Blind pot
        
        # 5. Call amount (BB)
        call_amount = game_state['current_bet'] - self.bet_this_round
        features['calls'] = round(call_amount / game_state['big_blind'], 2)
        
        # 6. Player count
        features['players'] = game_state['active_players_count']
        
        # 7. Continuation bet (simplified implementation)
        features['c_bet'] = 0  # Need more complex game state tracking
        
        # 8. Continuation bet history (simplified implementation)
        features['c_bet_his'] = 0
        
        # 9. Check-raise (simplified implementation)
        features['c_raise'] = 0
        
        # 10. Check-raise history (simplified implementation)
        features['c_raise_his'] = 0
        
        # 11. Big bet
        if call_amount > 0:
            if call_amount > game_state['pot'] * 0.8:
                features['b_bet'] = 2  # Very big bet
            elif call_amount > game_state['pot'] * 0.5:
                features['b_bet'] = 1  # Big bet
            else:
                features['b_bet'] = 0
        else:
            features['b_bet'] = 0
        
        # 12. Big bet history (simplified implementation)
        features['b_bet_his'] = 0
        
        # 13. Hand strength (0-100)
        features['strength'] = self.calculate_hand_strength(game_state['community_cards'])
        
        # 14-17. Community card wetness features
        wetness = self._calculate_wetness(game_state['community_cards'])
        features['wet_high'] = wetness['high']
        features['wet_pair'] = wetness['pair']
        features['wet_straight'] = wetness['straight']
        features['wet_flush'] = wetness['flush']
        
        return features
    
    def _calculate_wetness(self, community_cards):
        """Calculate community card wetness"""
        if not community_cards:
            return {'high': 0, 'pair': 0, 'straight': 0, 'flush': 0}
        
        # High card calculation
        high_cards = 0
        for card in community_cards:
            rank = card[:-1]
            if rank in ['A', 'K', 'Q', 'J']:
                high_cards += 1
        
        if high_cards >= 2:
            wet_high = 2
        elif high_cards == 1:
            wet_high = 1
        else:
            wet_high = 0
        
        # Pair calculation
        ranks = [card[:-1] for card in community_cards]
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        pairs = [r for r, c in rank_counts.items() if c >= 2]
        if len(pairs) >= 2:
            wet_pair = 2  # Two pair or three of a kind
        elif len(pairs) == 1:
            wet_pair = 1  # One pair
        else:
            wet_pair = 0
        
        # Straight calculation (simplified)
        wet_straight = 0
        if len(community_cards) >= 3:
            # Check for connected cards
            numeric_ranks = []
            for rank in ranks:
                if rank == 'A':
                    numeric_ranks.append(14)
                elif rank == 'K':
                    numeric_ranks.append(13)
                elif rank == 'Q':
                    numeric_ranks.append(12)
                elif rank == 'J':
                    numeric_ranks.append(11)
                elif rank == '10':
                    numeric_ranks.append(10)
                else:
                    numeric_ranks.append(int(rank))
            
            numeric_ranks.sort()
            for i in range(len(numeric_ranks) - 1):
                if numeric_ranks[i+1] - numeric_ranks[i] <= 2:
                    wet_straight = 1
                    break
        
        # Flush calculation
        suits = [card[-1] for card in community_cards]
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        if max_suit_count >= 3:
            wet_flush = 2
        elif max_suit_count == 2:
            wet_flush = 1
        else:
            wet_flush = 0
        
        return {
            'high': wet_high,
            'pair': wet_pair,
            'straight': wet_straight,
            'flush': wet_flush
        }
    
    def print_standard_features(self, features):
        """Print standard features"""
        print(f"\n🎯 {self.name}'s Standard Feature Analysis:")
        print(f"   📊 Stage: {features['stage']} ({self._get_stage_name(features['stage'])})")
        print(f"   🎭 Position: {features['pos']} ({self._get_position_name(features['pos'])})")
        print(f"   💰 Pot Size: {features['pots']} BB")
        print(f"   📍 Preflop Pot: {features['ppots']} BB")
        print(f"   📞 Call Amount: {features['calls']} BB")
        print(f"   👥 Active Players: {features['players']}")
        print(f"   🎲 Continuation Bet: {features['c_bet']}")
        print(f"   📈 Check-Raise: {features['c_raise']}")
        print(f"   💎 Big Bet: {features['b_bet']}")
        print(f"   🃏 Hand Strength: {features['strength']}/100")
        print(f"   🌊 Board Wetness:")
        print(f"      - High Cards: {features['wet_high']}")
        print(f"      - Pairs: {features['wet_pair']}")
        print(f"      - Straights: {features['wet_straight']}")
        print(f"      - Flushes: {features['wet_flush']}")
        
        # Decision advice
        self.print_decision_advice_from_features(features)
    
    def _get_stage_name(self, stage):
        stage_names = {0: "Pre-Flop", 1: "Flop", 2: "Turn", 3: "River"}
        return stage_names.get(stage, "Unknown")
    
    def _get_position_name(self, pos):
        pos_names = {0: "Early", 1: "Middle", 2: "Late"}
        return pos_names.get(pos, "Unknown")
    
    def print_decision_advice_from_features(self, features):
        """Provide decision advice based on standard features"""
        print(f"   💡 Decision Advice:")
        
        # Advice based on hand strength
        if features['strength'] >= 80:
            print(f"      🚀 Very strong hand, recommend aggressive action")
        elif features['strength'] >= 60:
            print(f"      ✅ Strong hand, can call or raise")
        elif features['strength'] >= 40:
            print(f"      🤔 Medium hand, act cautiously")
        else:
            print(f"      ⚠️  Weak hand, recommend folding")
        
        # Advice based on position
        if features['pos'] == 2:
            print(f"      🎯 Late position, can be more aggressive")
        elif features['pos'] == 1:
            print(f"      📍 Middle position, maintain balance")
        else:
            print(f"      ⚡ Early position, need to be cautious")
        
        # Advice based on pot odds
        if features['calls'] > 0:
            pot_odds = features['pots'] / features['calls']
            if pot_odds >= 3:
                print(f"      💎 Great pot odds, worth calling")
            elif pot_odds >= 2:
                print(f"      💰 Good pot odds, consider calling")
            else:
                print(f"      ⚠️  Poor pot odds, call cautiously")
        
        # Advice based on board wetness
        wetness_score = features['wet_high'] + features['wet_pair'] + features['wet_straight'] + features['wet_flush']
        if wetness_score >= 4:
            print(f"      🌊 Board very wet, beware of opponent's made hands")
        elif wetness_score >= 2:
            print(f"      💧 Board somewhat wet, watch for board changes")
        else:
            print(f"      🏜️ Board dry, good for bluffing")


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
                
                # Print decision features
                # game_state = {
                #     'community_cards': self.community_cards,
                #     'dealer_pos': self.dealer_pos,
                #     'total_players': len(self.players),
                #     'player_index': player_idx,
                #     'pot': self.pot,
                #     'current_bet': self.current_bet,
                #     'round_name': self.round_name,
                #     'active_players_count': len(self.get_active_players()),
                #     'big_blind': self.big_blind # Added for standard features
                # }
                # features = player.get_standard_features(game_state)
                # player.print_standard_features(features)
                
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