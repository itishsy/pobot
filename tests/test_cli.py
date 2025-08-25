#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动执行10局完整德州扑克游戏的测试文件
每局游戏前生成游戏对象，每个玩家行动前生成游戏状态并输出到JSON文件
"""

import sys
import os
import json
import random
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from train.cli import PokerGame, Player
from models.game_state import GameState
from models.game_player import GamePlayer


class AutoPokerGame:
    """自动德州扑克游戏类"""
    
    def __init__(self, player_names, small_blind=1, big_blind=2):
        self.player_names = player_names
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.game_states = []
        self.current_game_code = None
        self.current_stage = 0
        self.current_round = 0
        
    def generate_game_code(self):
        """生成游戏代码"""
        return datetime.now().strftime('%Y%m%d%H%M%S')
    
    def create_game_state(self, game, player, player_idx, action=None):
        """为当前玩家创建游戏状态"""
        game_state = GameState()
        
        # 基本信息
        game_state.code = self.current_game_code
        game_state.stage = self.current_stage
        game_state.round = self.current_round
        
        # 当前玩家信息
        game_state.name = player.name
        game_state.hand = player.hand
        game_state.position = player_idx
        game_state.stack = player.chips
        
        # 牌面信息
        game_state.community_cards = game.community_cards
        game_state.pot = game.pot
        game_state.call = game.current_bet - player.bet_this_round
        
        # 其他玩家信息
        active_players = game.get_active_players()
        other_players = []
        
        for i in range(len(game.players)):
            if i != player_idx and not game.players[i].folded:
                other_player = game.players[i]
                gp = GamePlayer(
                    name=other_player.name,
                    position=i,
                    stack=other_player.chips,
                    action=other_player.action or '',
                    active=1 if not other_player.folded else 0,
                    amount=other_player.bet_this_round
                )
                other_players.append(gp)
        
        # 设置其他玩家信息
        for i, gp in enumerate(other_players[:5]):
            if i == 0:
                game_state.player1 = gp.to_dict()
            elif i == 1:
                game_state.player2 = gp.to_dict()
            elif i == 2:
                game_state.player3 = gp.to_dict()
            elif i == 3:
                game_state.player4 = gp.to_dict()
            elif i == 4:
                game_state.player5 = gp.to_dict()
        
        # 计算手牌强度（简化版本）
        game_state.strength = self.calculate_hand_strength(player.hand, game.community_cards)
        
        # 设置玩家列表
        game_state.pls = other_players
        
        # 设置行动
        if action is not None:
            game_state.action = action
        
        return game_state
    
    def calculate_hand_strength(self, hand, community_cards):
        """计算手牌强度（0-100）"""
        if not hand or len(hand) < 2:
            return 0
        
        # 基础点数计算
        hand_value = 0
        
        for card in hand:
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
        
        # 同花奖励
        if len(hand) == 2 and hand[0][-1] == hand[1][-1]:
            hand_value += 10
        
        # 对子奖励
        if len(hand) == 2 and hand[0][:-1] == hand[1][:-1]:
            hand_value += 20
        
        # 连接牌奖励
        if len(hand) == 2:
            rank1 = hand[0][:-1]
            rank2 = hand[1][:-1]
            if rank1 == 'A' and rank2 in ['K', 'Q']:
                hand_value += 15
            elif rank1 == 'K' and rank2 == 'Q':
                hand_value += 12
            elif rank1 == 'Q' and rank2 == 'J':
                hand_value += 10
        
        # 标准化到0-100范围
        return min(hand_value * 2, 100)
    
    def auto_player_action(self, game, player, player_idx):
        """自动玩家行动"""
        valid_actions = game.get_valid_actions(player)
        
        # 简单的AI策略
        call_amount = game.current_bet - player.bet_this_round
        
        # 基于手牌强度决定行动
        hand_strength = self.calculate_hand_strength(player.hand, game.community_cards)
        
        # 生成游戏状态
        game_state = self.create_game_state(game, player, player_idx)
        self.game_states.append(game_state)
        
        # 决定行动
        if hand_strength >= 80:
            # 很强的手牌，加注
            action = 2  # Raise
            if 2 in valid_actions:
                raise_amount = min(max(game.big_blind, call_amount * 2), player.chips)
            else:
                action = 1  # Call
                raise_amount = 0
        elif hand_strength >= 60:
            # 强手牌，跟注
            action = 1  # Call
            raise_amount = 0
        elif hand_strength >= 40:
            # 中等手牌，根据底池赔率决定
            if call_amount == 0:
                action = 0  # Check
                raise_amount = 0
            elif call_amount <= game.pot * 0.3:
                action = 1  # Call
                raise_amount = 0
            else:
                action = 0  # Fold
                raise_amount = 0
        else:
            # 弱手牌，弃牌或过牌
            if call_amount == 0:
                action = 0  # Check
                raise_amount = 0
            else:
                action = 0  # Fold
                raise_amount = 0
        
        # 确保行动有效
        if action not in valid_actions:
            if 1 in valid_actions:  # 如果可以跟注
                action = 1
                raise_amount = 0
            else:
                action = 0  # 过牌或弃牌
                raise_amount = 0
        
        # 执行行动
        game.process_player_action(player, action, raise_amount)
        
        # 更新游戏状态中的行动
        game_state.action = action
        
        return action, raise_amount
    
    def play_auto_round(self, game):
        """自动执行一轮游戏"""
        print(f"\n=== 开始 {game.round_name} 阶段 ===")
        
        # 更新阶段信息
        if game.round_name == "Pre-Flop":
            self.current_stage = 0
        elif game.round_name == "Flop":
            self.current_stage = 1
        elif game.round_name == "Turn":
            self.current_stage = 2
        elif game.round_name == "River":
            self.current_stage = 3
        
        # 重置轮次
        self.current_round = 0
        
        if game.round_name == "Pre-Flop":
            start_pos = (game.dealer_pos + 3) % len(game.players)  # UTG位置
        else:
            start_pos = (game.dealer_pos + 1) % len(game.players)  # SB位置
        
        last_raiser = None
        first_to_act = True
        
        while not game.betting_round_complete():
            self.current_round += 1
            
            for i in range(len(game.players)):
                player_idx = (start_pos + i) % len(game.players)
                player = game.players[player_idx]
                
                if player.folded or player.all_in:
                    continue
                
                if not first_to_act and player_idx == last_raiser:
                    game.stage_complete = True
                    break
                
                print(f"\n{player.name} 行动 (手牌: {' '.join(player.hand)})")
                print(f"筹码: ${player.chips}, 当前下注: ${player.bet_this_round}")
                print(f"底池: ${game.pot}, 需要跟注: ${game.current_bet - player.bet_this_round}")
                
                # 自动玩家行动
                action, raise_amount = self.auto_player_action(game, player, player_idx)
                
                if action == 2:  # 加注
                    last_raiser = player_idx
                
                if len(game.get_active_players()) <= 1:
                    game.stage_complete = True
                    break
            
            first_to_act = False
        
        # 收集下注
        game.collect_bets()
    
    def play_auto_game(self, game):
        """自动执行一局完整游戏"""
        print(f"\n🎮 开始新游戏: {self.current_game_code}")
        
        # Pre-Flop
        game.deal_hole_cards()
        game.post_blinds()
        self.play_auto_round(game)
        
        # Flop
        if len(game.get_active_players()) >= 2:
            game.reset_for_new_stage()
            game.deal_community_cards(3)
            self.play_auto_round(game)
        
        # Turn
        if len(game.get_active_players()) >= 2:
            game.reset_for_new_stage()
            game.deal_community_cards(1)
            self.play_auto_round(game)
        
        # River
        if len(game.get_active_players()) >= 2:
            game.reset_for_new_stage()
            game.deal_community_cards(1)
            self.play_auto_round(game)
        
        # 摊牌
        try:
            from train.cal import distribute_pot
            result = distribute_pot(game.get_active_players(), game.community_cards, game.pot)
            print(f"\n🏆 摊牌结果: {result.get('message', '游戏结束')}")
        except ImportError:
            print("\n🏆 游戏结束，无法计算摊牌结果")
        
        # 准备下一手
        game.community_cards = []
        game.dealer_pos = (game.dealer_pos + 1) % len(game.players)
        for player in game.players:
            player.folded = False
            player.all_in = False
            player.bet_this_round = 0
            player.total_bet = 0
            player.hand = []
        
        game.deck = game._create_deck()
        game.shuffle_deck()
        game.pot = 0
        game.current_bet = 0
        game.round_name = "Pre-Flop"
    
    def save_game_states_to_json(self, filename="game_state.json"):
        """将游戏状态保存到JSON文件"""
        states_data = []
        
        for state in self.game_states:
            state_dict = {
                'code': state.code,
                'stage': state.stage,
                'round': state.round,
                'name': state.name,
                'hand': state.hand,
                'position': state.position,
                'stack': state.stack,
                'community_cards': state.community_cards,
                'pot': state.pot,
                'call': state.call,
                'player1': state.player1,
                'player2': state.player2,
                'player3': state.player3,
                'player4': state.player4,
                'player5': state.player5,
                'strength': state.strength,
                'action': state.action,
                'timestamp': datetime.now().isoformat()
            }
            states_data.append(state_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(states_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 游戏状态已保存到 {filename}")
        print(f"📊 总共记录了 {len(states_data)} 个游戏状态")
    
    def run_auto_games(self, num_games=10):
        """运行指定数量的自动游戏"""
        print(f"🚀 开始自动执行 {num_games} 局德州扑克游戏")
        
        for game_num in range(1, num_games + 1):
            print(f"\n{'='*50}")
            print(f"🎯 第 {game_num} 局游戏")
            print(f"{'='*50}")
            
            # 生成新的游戏代码
            self.current_game_code = self.generate_game_code()
            
            # 创建新游戏
            game = PokerGame(self.player_names, self.small_blind, self.big_blind)
            
            # 执行游戏
            self.play_auto_game(game)
            
            # 移除没有筹码的玩家
            game.players = [p for p in game.players if p.chips > 0]
            if len(game.players) < 2:
                print(f"🎮 游戏结束 - 只剩一名玩家: {game.players[0].name} (${game.players[0].chips})")
                break
            
            print(f"🎮 第 {game_num} 局游戏完成")
            print(f"剩余玩家: {len(game.players)}")
            for player in game.players:
                print(f"  {player.name}: ${player.chips}")
        
        # 保存所有游戏状态
        self.save_game_states_to_json()


def main():
    """主函数"""
    print("🎲 德州扑克自动游戏测试")
    print("=" * 50)
    
    # 玩家名称
    player_names = ["玩家1", "玩家2", "玩家3", "玩家4", "玩家5", "玩家6"]
    
    # 创建自动游戏实例
    auto_game = AutoPokerGame(player_names, small_blind=1, big_blind=2)
    
    # 运行10局游戏
    auto_game.run_auto_games(num_games=10)
    
    print("\n🎉 所有游戏完成！")


if __name__ == "__main__":
    main()
