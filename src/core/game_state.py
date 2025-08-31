from re import A
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ActionType(Enum):
    """动作类型枚举"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

@dataclass
class Action:
    """动作记录类"""
    player_id: str  # 执行动作的玩家ID
    action_type: ActionType  # 动作类型
    amount: int  # 下注/加注金额(对于call/fold/check为0)


@dataclass
class Player:
    """玩家信息类"""
    id: str  # 玩家唯一标识
    name: str  # 玩家昵称
    position: int # 玩家位置
    hand: List[str] # 玩家手牌
    stack: int  # 玩家剩余筹码量
    current_bet: int  # 玩家在当前回合已下注额
    is_in_hand: bool  # 玩家是否仍在牌局中
    is_active: bool  # 玩家是否可行动(未弃牌且未全下)
    is_dealer: bool  # 玩家是否为庄家
    is_small_blind: bool  # 玩家是否为小盲
    is_big_blind: bool  # 玩家是否为大盲
    bet_this_round: int # 玩家在当前回合已下注额
    total_bet: int  # Total bet in this hand
    cards: Optional[List[str]] = None  # 玩家的手牌(仅对自己的牌可见)
    action: Action # 玩家采取的动作类型和金额
    position: int # 玩家位置# 玩家上一轮动作
    vpip: float = 0.0  # 玩家自愿入池率统计
    pfr: float = 0.0  # 玩家翻前加注率统计
    aggression_factor: float = 0.0  # 玩家攻击性统计
    three_bet_percent: float = 0.0  # 玩家3Bet频率统计

@dataclass
class Round:
    """游戏轮次类 - 以当前玩家的视角，记录每一个行动轮次(同一阶段内可能有多轮下注)的牌面"""
    id: int # 时间戳
    stage: int  # 阶段: 0: preflop, 1: flop, 2: turn, 3: river
    current_bet_round: int = 0  # 当前下注轮次(同一阶段内可能有多轮下注)
    community_cards: List[str] = []  # 公共牌
    pot: int = 0  # 当前底池大小
    call: int = 0  # 当前需要跟注的金额
    min_raise: int = 0  # 最小加注额度
    max_raise: int = 0  # 最大加注额度(通常为玩家剩余筹码)

    current_player: Player # 当前玩家
    active_opponents: List[Player] = []  # 当前活跃玩家信息


@dataclass
class GameState:
    """游戏状态类 - 以当前玩家的视角，记录牌桌可识别到的信息"""
    
    table_id: str = "" # 牌桌ID
    big_blind: int = 0 # 大盲金额
    total_players: int = 6 # 入座玩家数量
    current_player: Player = None # 当前玩家
    opponents: List[Player] = [] # 其他玩家信息
    rounds: List[Round] = [] # 当局游戏所有状态，包含每个阶段的所有信息
    reward: int = 0 # 当前玩家获得的奖励

    def get_action_history(self) -> List[Action]:
        """获取本手牌所有行动记录"""
        action_history = []
        for round in self.rounds:
            action_history.extend(round.action_history)
        return action_history
    
    def get_current_street_actions(self) -> List[Action]:
        """获取当前阶段的行动记录"""
        current_street_actions = []
        for round in self.rounds:
            current_street_actions.extend(round.current_street_actions)
        return current_street_actions
    
    def get_preflop_raiser(self) -> Optional[str]:
        """获取翻前最后加注者"""
        for round in self.rounds:
            if round.stage == 0:
                return round.preflop_raiser
        return None
    
    def get_aggressor(self) -> Optional[str]:
        """获取当前回合最后一个激进者(下注/加注者)"""
        for round in self.rounds:
            if round.stage == 0:
                return round.aggressor
        return None
    
    def get_last_raiser(self) -> Optional[str]:
        """获取最后一个加注者"""
        for round in self.rounds:
            if round.stage == 0:
                return round.last_raiser
        return None
