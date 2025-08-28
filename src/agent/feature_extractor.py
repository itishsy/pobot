import numpy as np
from typing import Dict, List
from enum import Enum

class FeatureExtractor:
    """从GameState中提取特征用于强化学习模型"""
    
    def __init__(self):
        self.feature_dim = 87  # 总特征维度
        self.feature_names = []  # 特征名称列表(用于调试和分析)
        
    def extract_features(self, game_state) -> np.ndarray:
        """
        将GameState转换为特征向量
        
        参数:
            game_state: 游戏状态对象
            
        返回:
            np.ndarray: 特征向量，形状为(87,)
        """
        features = []
        
        # 1. 手牌强度特征 (9维)
        hand_strength_features = self._extract_hand_strength_features(game_state)
        features.extend(hand_strength_features)
        
        # 2. 位置特征 (6维)
        position_features = self._extract_position_features(game_state)
        features.extend(position_features)
        
        # 3. 底池与筹码特征 (8维)
        pot_stack_features = self._extract_pot_stack_features(game_state)
        features.extend(pot_stack_features)
        
        # 4. 对手建模特征 (36维)
        opponent_features = self._extract_opponent_features(game_state)
        features.extend(opponent_features)
        
        # 5. 行动历史特征 (15维)
        action_history_features = self._extract_action_history_features(game_state)
        features.extend(action_history_features)
        
        # 6. 游戏阶段特征 (5维)
        game_stage_features = self._extract_game_stage_features(game_state)
        features.extend(game_stage_features)
        
        # 7. 综合决策特征 (8维)
        decision_features = self._extract_decision_features(game_state)
        features.extend(decision_features)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_hand_strength_features(self, game_state) -> List[float]:
        """提取手牌强度相关特征"""
        features = []
        hero = game_state.get_hero()
        
        # 1. 手牌绝对强度 (使用预计算的值)
        if hero and hero.cards:
            hand_strength = self._calculate_hand_strength(hero.cards, game_state.community_cards)
            features.append(hand_strength)
            
            # 2. 手牌发展潜力 (听牌能力)
            draw_potential = self._calculate_draw_potential(hero.cards, game_state.community_cards)
            features.append(draw_potential)
            
            # 3-5. 手牌类型 (一对、两对、三条等)
            hand_type_features = self._encode_hand_type(hero.cards, game_state.community_cards)
            features.extend(hand_type_features)
            
            # 6. 牌面联动性 (湿/干程度)
            board_texture = self._calculate_board_texture(game_state.community_cards)
            features.append(board_texture)
            
            # 7-9. 手牌与牌面匹配度
            hand_board_compatibility = self._calculate_hand_board_compatibility(
                hero.cards, game_state.community_cards)
            features.extend(hand_board_compatibility)
        else:
            # 手牌不可见时的填充值
            features.extend([0.0] * 9)
            
        return features
    
    def _extract_position_features(self, game_state) -> List[float]:
        """提取位置相关特征"""
        features = []
        hero = game_state.get_hero()
        
        if hero:
            # 1. 绝对位置 (0=按钮位, 5=枪口位)
            abs_position = game_state.get_relative_position(hero.id)
            features.append(abs_position / 5.0)  # 归一化到[0,1]
            
            # 2. 位置优势 (相对于尚未行动的玩家)
            position_advantage = self._calculate_position_advantage(game_state, hero.id)
            features.append(position_advantage)
            
            # 3-6. 相对于特定对手的位置
            opponents = game_state.get_opponents()
            for i, opp in enumerate(opponents[:4]):  # 最多考虑4个对手
                rel_pos = (game_state.get_relative_position(hero.id) - 
                          game_state.get_relative_position(opp.id)) % 6
                features.append(rel_pos / 5.0)  # 归一化
            # 如果对手不足4个，用0填充
            features.extend([0.0] * (4 - min(4, len(opponents))))
        else:
            features.extend([0.0] * 6)
            
        return features
    
    def _extract_pot_stack_features(self, game_state) -> List[float]:
        """提取底池和筹码相关特征"""
        features = []
        hero = game_state.get_hero()
        
        if hero:
            # 1. 底池赔率
            pot_odds = game_state.get_pot_odds(game_state.bet_amount)
            features.append(pot_odds)
            
            # 2. 隐含赔率估计
            implied_odds = self._estimate_implied_odds(game_state, hero.id)
            features.append(implied_odds)
            
            # 3. 筹码量与底池比例 (SPR)
            spr = game_state.get_stack_to_pot_ratio(hero.id)
            features.append(min(spr, 10.0) / 10.0)  # 截断并归一化
            
            # 4. 有效筹码量
            effective_stack = game_state.get_effective_stack(hero.id)
            max_buyin = game_state.max_buy_in if game_state.max_buy_in > 0 else 200
            features.append(effective_stack / max_buyin)  # 归一化
            
            # 5. 己方筹码占比
            total_chips = sum(p.stack for p in game_state.players.values() if p.is_in_hand)
            hero_stack_ratio = hero.stack / total_chips if total_chips > 0 else 0
            features.append(hero_stack_ratio)
            
            # 6. 跟注所需筹码占比
            call_ratio = game_state.bet_amount / hero.stack if hero.stack > 0 else 0
            features.append(min(call_ratio, 1.0))
            
            # 7. 已投入筹码占比
            invested_ratio = (hero.current_bet + game_state.bet_amount) / (
                hero.stack + hero.current_bet + game_state.bet_amount) if hero.stack > 0 else 0
            features.append(invested_ratio)
            
            # 8. 最小加注占比
            min_raise_ratio = game_state.min_raise / hero.stack if hero.stack > 0 else 0
            features.append(min(min_raise_ratio, 1.0))
        else:
            features.extend([0.0] * 8)
            
        return features
    
    def _extract_opponent_features(self, game_state) -> List[float]:
        """提取对手建模相关特征"""
        features = []
        opponents = game_state.get_opponents()
        hero = game_state.get_hero()
        
        if not hero:
            return [0.0] * 36
        
        # 对每个对手提取特征 (最多6个对手，每个6维)
        for i, opp in enumerate(opponents[:6]):
            # 1. VPIP (自愿入池率)
            features.append(opp.vpip)
            
            # 2. PFR (翻前加注率)
            features.append(opp.pfr)
            
            # 3. 攻击性系数
            features.append(min(opp.aggression_factor, 5.0) / 5.0)  # 归一化
            
            # 4. 3Bet频率
            features.append(opp.three_bet_percent)
            
            # 5. 面对持续下注弃牌率
            fold_to_cbet = self._get_opponent_stat(opp.id, "fold_to_cbet", 0.5)
            features.append(fold_to_cbet)
            
            # 6. 手牌范围内估计的强度
            opp_range_strength = self._estimate_opponent_range_strength(game_state, opp.id)
            features.append(opp_range_strength)
        
        # 如果对手不足6个，用默认值填充
        features.extend([0.5] * (6 * (6 - min(6, len(opponents)))))
        
        return features
    
    def _extract_action_history_features(self, game_state) -> List[float]:
        """提取行动历史相关特征"""
        features = []
        
        # 1-3. 最近三个动作的类型 (one-hot编码)
        recent_actions = game_state.get_previous_actions(3)
        for i in range(3):
            if i < len(recent_actions):
                action_type = recent_actions[i].action_type
                # 将动作类型映射为数值
                action_map = {
                    "fold": 0.0, "check": 0.25, "call": 0.5, 
                    "bet": 0.75, "raise": 1.0, "all_in": 1.0
                }
                features.append(action_map.get(action_type, 0.0))
            else:
                features.append(0.0)  # 无动作
        
        # 4-6. 最近三个动作的激进程度
        for i in range(3):
            if i < len(recent_actions):
                aggressiveness = self._calculate_action_aggressiveness(recent_actions[i], game_state)
                features.append(aggressiveness)
            else:
                features.append(0.0)
        
        # 7-9. 当前回合的行动数量
        actions_in_street = len(game_state.current_street_actions)
        features.append(min(actions_in_street, 5) / 5.0)  # 归一化
        
        # 当前回合的加注次数
        raises_in_street = sum(1 for a in game_state.current_street_actions 
                              if a.action_type in ["raise", "bet"])
        features.append(min(raises_in_street, 3) / 3.0)  # 归一化
        
        # 当前回合的跟注次数
        calls_in_street = sum(1 for a in game_state.current_street_actions 
                             if a.action_type == "call")
        features.append(min(calls_in_street, 3) / 3.0)  # 归一化
        
        # 10-12. 翻前加注者信息
        preflop_raiser = game_state.preflop_raiser
        if preflop_raiser:
            # 是否是英雄自己
            features.append(1.0 if preflop_raiser == game_state.get_hero().id else 0.0)
            # 加注者的位置优势
            raiser_pos = game_state.get_relative_position(preflop_raiser)
            features.append(raiser_pos / 5.0)
            # 加注者的激进程度
            raiser_aggression = self._get_player_aggression(preflop_raiser, game_state)
            features.append(raiser_aggression)
        else:
            features.extend([0.0] * 3)
        
        # 13-15. 最后激进者信息
        last_aggressor = game_state.aggressor
        if last_aggressor:
            # 是否是英雄自己
            features.append(1.0 if last_aggressor == game_state.get_hero().id else 0.0)
            # 激进者的位置优势
            aggressor_pos = game_state.get_relative_position(last_aggressor)
            features.append(aggressor_pos / 5.0)
            # 激进动作的强度
            last_action = game_state.current_street_actions[-1] if game_state.current_street_actions else None
            aggressiveness = self._calculate_action_aggressiveness(last_action, game_state) if last_action else 0.0
            features.append(aggressiveness)
        else:
            features.extend([0.0] * 3)
            
        return features
    
    def _extract_game_stage_features(self, game_state) -> List[float]:
        """提取游戏阶段相关特征"""
        features = []
        
        # 1-4. 游戏阶段 (one-hot编码)
        stage_map = {
            "preflop": [1, 0, 0, 0],
            "flop": [0, 1, 0, 0],
            "turn": [0, 0, 1, 0],
            "river": [0, 0, 0, 1]
        }
        features.extend(stage_map.get(game_state.street.value, [0, 0, 0, 0]))
        
        # 5. 是否接近摊牌
        features.append(1.0 if game_state.street.value in ["turn", "river"] else 0.0)
        
        return features
    
    def _extract_decision_features(self, game_state) -> List[float]:
        """提取综合决策相关特征"""
        features = []
        hero = game_state.get_hero()
        
        if not hero:
            return [0.0] * 8
        
        # 1. 当前决策紧迫性
        urgency = self._calculate_decision_urgency(game_state)
        features.append(urgency)
        
        # 2. 风险/回报比
        risk_reward = self._calculate_risk_reward_ratio(game_state, hero.id)
        features.append(risk_reward)
        
        # 3. 潜在弃牌率 (对手可能弃牌的概率)
        fold_equity = self._estimate_fold_equity(game_state)
        features.append(fold_equity)
        
        # 4. 期望价值 (粗略估计)
        expected_value = self._estimate_expected_value(game_state, hero.id)
        features.append(expected_value)
        
        # 5. 资金管理考虑
        bankroll_factor = self._calculate_bankroll_factor(game_state, hero.id)
        features.append(bankroll_factor)
        
        # 6. 牌桌动态 (紧/松程度)
        table_dynamics = self._assess_table_dynamics(game_state)
        features.append(table_dynamics)
        
        # 7. 时间压力
        time_pressure = min(game_state.time_bank / 30.0, 1.0)  # 假设30秒为完整时间银行
        features.append(time_pressure)
        
        # 8. 整体信心水平
        confidence = self._calculate_confidence_level(game_state, hero.id)
        features.append(confidence)
        
        return features
    
    # 以下是一些辅助方法的具体实现框架
    def _calculate_hand_strength(self, cards, community_cards) -> float:
        """计算手牌强度 (0-1)"""
        # 实现手牌强度计算逻辑
        # 可以使用蒙特卡洛模拟或预计算的查表
        return 0.5  # 示例值
    
    def _calculate_draw_potential(self, cards, community_cards) -> float:
        """计算听牌潜力 (0-1)"""
        # 实现听牌潜力计算逻辑
        return 0.5  # 示例值
    
    def _encode_hand_type(self, cards, community_cards) -> List[float]:
        """编码手牌类型 (6维)"""
        # 实现手牌类型编码逻辑
        return [0.0] * 6  # 示例值
    
    # 其他辅助方法类似，需要根据具体游戏逻辑实现...