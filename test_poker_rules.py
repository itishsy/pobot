#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
德州扑克规则测试类
测试cli.py中的游戏逻辑是否符合标准德扑规则
"""

import unittest
from unittest.mock import patch
import sys
import io
from src.train.cli import PokerGame, Player

class PokerRulesTest(unittest.TestCase):
    """德州扑克规则测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.player_names = ["Player1", "Player2", "Player3", "Player4", "Player5", "Player6"]
        self.game = PokerGame(self.player_names)
    
    def test_initial_game_state(self):
        """测试游戏初始状态"""
        # 检查玩家数量
        self.assertEqual(len(self.game.players), 6)
        
        # 检查初始筹码
        for player in self.game.players:
            self.assertEqual(player.chips, 100)
            self.assertFalse(player.folded)
            self.assertFalse(player.all_in)
            self.assertEqual(player.bet_this_round, 0)
            self.assertEqual(player.total_bet, 0)
        
        # 检查牌堆
        self.assertEqual(len(self.game.deck), 52)
        
        # 检查盲注设置
        self.assertEqual(self.game.small_blind, 1)
        self.assertEqual(self.game.big_blind, 2)
    
    def test_deck_creation(self):
        """测试牌堆创建"""
        deck = self.game._create_deck()
        self.assertEqual(len(deck), 52)
        
        # 检查花色和点数
        ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
        suits = ['♥','♦','♠','♣']
        
        for rank in ranks:
            for suit in suits:
                card = rank + suit
                self.assertIn(card, deck)
        
        # 检查没有重复
        self.assertEqual(len(set(deck)), 52)
    
    def test_blind_posting(self):
        """测试盲注收取"""
        # 设置庄家位置
        self.game.dealer_pos = 0
        
        # 收取盲注
        self.game.post_blinds()
        
        # 小盲注位置 (dealer + 1) % 6 = 1
        sb_pos = 1
        sb_player = self.game.players[sb_pos]
        self.assertEqual(sb_player.bet_this_round, 1)
        self.assertEqual(sb_player.chips, 99)
        
        # 大盲注位置 (dealer + 2) % 6 = 2
        bb_pos = 2
        bb_player = self.game.players[bb_pos]
        self.assertEqual(bb_player.bet_this_round, 2)
        self.assertEqual(bb_player.chips, 98)
        
        # 检查底池
        self.assertEqual(self.game.pot, 3)
        self.assertEqual(self.game.current_bet, 2)
    
    def test_hole_cards_dealing(self):
        """测试发手牌"""
        initial_deck_size = len(self.game.deck)
        
        self.game.deal_hole_cards()
        
        # 检查每个玩家都有2张牌
        for player in self.game.players:
            self.assertEqual(len(player.hand), 2)
        
        # 检查牌堆减少了12张牌 (6玩家 × 2张)
        self.assertEqual(len(self.game.deck), initial_deck_size - 12)
        
        # 检查手牌不重复
        all_cards = []
        for player in self.game.players:
            all_cards.extend(player.hand)
        self.assertEqual(len(set(all_cards)), 12)
    
    def test_community_cards_dealing(self):
        """测试发公共牌"""
        # 翻牌 - 发3张
        self.game.deal_community_cards(3)
        self.assertEqual(len(self.game.community_cards), 3)
        self.assertEqual(self.game.round_name, "Flop")
        
        # 转牌 - 发1张
        self.game.deal_community_cards(1)
        self.assertEqual(len(self.game.community_cards), 4)
        self.assertEqual(self.game.round_name, "Turn")
        
        # 河牌 - 发1张
        self.game.deal_community_cards(1)
        self.assertEqual(len(self.game.community_cards), 5)
        self.assertEqual(self.game.round_name, "River")
        
        # 检查牌堆减少
        self.assertEqual(len(self.game.deck), 52 - 12 - 5)  # 52 - 手牌 - 公共牌
    
    def test_valid_actions(self):
        """测试有效操作"""
        # 设置当前下注
        self.game.current_bet = 10
        
        # 玩家1还没有下注
        player1 = self.game.players[0]
        player1.bet_this_round = 0
        
        valid_actions = self.game.get_valid_actions(player1)
        
        # 应该包含：Fold(0), Call(1), Raise(2)
        self.assertIn(0, valid_actions)  # Fold
        self.assertIn(1, valid_actions)  # Call
        self.assertIn(2, valid_actions)  # Raise
        
        # 玩家1跟注后
        player1.bet_this_round = 10
        valid_actions = self.game.get_valid_actions(player1)
        
        # 应该包含：Check(0), Raise(2)
        self.assertIn(0, valid_actions)  # Check
        self.assertIn(2, valid_actions)  # Raise
        self.assertNotIn(1, valid_actions)  # 不能Call
    
    def test_player_actions(self):
        """测试玩家操作"""
        # 设置游戏状态
        self.game.current_bet = 10
        player = self.game.players[0]
        player.chips = 50
        player.bet_this_round = 0
        
        # 测试弃牌
        self.game.process_player_action(player, 0)
        self.assertTrue(player.folded)
        self.assertEqual(player.action, 'Fold')
        
        # 重置玩家状态
        player.folded = False
        player.action = None
        player.bet_this_round = 0
        
        # 测试跟注
        self.game.process_player_action(player, 1)
        self.assertEqual(player.bet_this_round, 10)
        self.assertEqual(player.chips, 40)
        self.assertEqual(player.action, 'Call')
        self.assertEqual(self.game.pot, 13)  # 之前3 + 新10
        
        # 重置
        player.bet_this_round = 0
        player.chips = 40
        self.game.pot = 3
        
        # 测试加注
        self.game.process_player_action(player, 2, 5)  # 加注5
        self.assertEqual(player.bet_this_round, 15)  # 跟注10 + 加注5
        self.assertEqual(player.chips, 25)
        self.assertEqual(self.game.current_bet, 15)
        self.assertEqual(player.action, 'Raise')
    
    def test_betting_round_completion(self):
        """测试下注轮完成条件"""
        # 设置所有玩家都跟注
        for player in self.game.players:
            player.bet_this_round = 10
        
        self.game.current_bet = 10
        self.game.is_new_stage = False
        
        # 应该完成下注轮
        self.assertTrue(self.game.betting_round_complete())
        
        # 设置一个玩家还没跟注
        self.game.players[0].bet_this_round = 5
        self.assertFalse(self.game.betting_round_complete())
    
    def test_all_in_scenarios(self):
        """测试全下场景"""
        player = self.game.players[0]
        player.chips = 5
        self.game.current_bet = 10
        player.bet_this_round = 0
        
        # 玩家全下跟注
        self.game.process_player_action(player, 1)
        self.assertTrue(player.all_in)
        self.assertEqual(player.chips, 0)
        self.assertEqual(player.bet_this_round, 5)
    
    def test_game_round_progression(self):
        """测试游戏轮次进展"""
        # 模拟完整的游戏流程
        self.game.dealer_pos = 0
        
        # 预翻牌
        self.game.reset_for_new_stage()
        self.game.deal_hole_cards()
        self.game.post_blinds()
        self.assertEqual(self.game.round_name, "Pre-Flop")
        self.assertEqual(len(self.game.community_cards), 0)
        
        # 翻牌
        self.game.reset_for_new_stage()
        self.game.deal_community_cards(3)
        self.assertEqual(self.game.round_name, "Flop")
        self.assertEqual(len(self.game.community_cards), 3)
        
        # 转牌
        self.game.reset_for_new_stage()
        self.game.deal_community_cards(1)
        self.assertEqual(self.game.round_name, "Turn")
        self.assertEqual(len(self.game.community_cards), 4)
        
        # 河牌
        self.game.reset_for_new_stage()
        self.game.deal_community_cards(1)
        self.assertEqual(self.game.round_name, "River")
        self.assertEqual(len(self.game.community_cards), 5)
    
    def test_player_elimination(self):
        """测试玩家淘汰"""
        # 设置一个玩家筹码为0
        player = self.game.players[0]
        player.chips = 0
        player.folded = True
        
        # 检查活跃玩家
        active_players = self.game.get_active_players()
        self.assertEqual(len(active_players), 5)
        self.assertNotIn(player, active_players)
    
    def test_pot_distribution(self):
        """测试底池分配"""
        # 设置底池
        self.game.pot = 100
        
        # 模拟获胜者
        winner = self.game.players[0]
        winner.chips = 50
        
        # 分配底池
        winner.chips += self.game.pot
        self.assertEqual(winner.chips, 150)
        self.assertEqual(self.game.pot, 100)  # 底池应该被清空
    
    def test_invalid_actions(self):
        """测试无效操作"""
        player = self.game.players[0]
        player.chips = 5
        self.game.current_bet = 10
        player.bet_this_round = 0
        
        # 尝试加注超过筹码
        self.game.process_player_action(player, 2, 10)
        self.assertTrue(player.all_in)
        self.assertEqual(player.chips, 0)
    
    def test_game_reset(self):
        """测试游戏重置"""
        # 设置游戏状态
        self.game.pot = 100
        self.game.current_bet = 10
        self.game.round_name = "River"
        self.game.community_cards = ["A♥", "K♥", "Q♥", "J♥", "10♥"]
        
        # 重置游戏
        self.game.community_cards = []
        self.game.dealer_pos = (self.game.dealer_pos + 1) % len(self.game.players)
        self.game.pot = 0
        self.game.current_bet = 0
        self.game.round_name = "Pre-Flop"
        
        # 验证重置
        self.assertEqual(self.game.pot, 0)
        self.assertEqual(self.game.current_bet, 0)
        self.assertEqual(self.game.round_name, "Pre-Flop")
        self.assertEqual(len(self.game.community_cards), 0)
        self.assertEqual(self.game.dealer_pos, 1)

def run_comprehensive_test():
    """运行综合测试"""
    print("开始运行德州扑克规则综合测试...")
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(PokerRulesTest)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print(f"\n测试结果总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result

if __name__ == "__main__":
    run_comprehensive_test()
