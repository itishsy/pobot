from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class Street(Enum):
    """游戏阶段枚举"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

class ActionType(Enum):
    """动作类型枚举"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

@dataclass
class Player:
    """玩家信息类"""
    id: str  # 玩家唯一标识
    name: str  # 玩家昵称
    stack: int  # 玩家剩余筹码量
    current_bet: int  # 玩家在当前回合已下注额
    is_in_hand: bool  # 玩家是否仍在牌局中
    is_active: bool  # 玩家是否可行动(未弃牌且未全下)
    is_dealer: bool  # 玩家是否为庄家
    is_small_blind: bool  # 玩家是否为小盲
    is_big_blind: bool  # 玩家是否为大盲
    cards: Optional[List[str]] = None  # 玩家的手牌(仅对自己的牌可见)
    last_action: Optional[Tuple[ActionType, int]] = None  # 玩家上一轮动作
    vpip: float = 0.0  # 玩家自愿入池率统计
    pfr: float = 0.0  # 玩家翻前加注率统计
    aggression_factor: float = 0.0  # 玩家攻击性统计
    three_bet_percent: float = 0.0  # 玩家3Bet频率统计

@dataclass
class Action:
    """动作记录类"""
    player_id: str  # 执行动作的玩家ID
    action_type: ActionType  # 动作类型
    amount: int  # 下注/加注金额(对于call/fold/check为0)
    street: Street  # 动作发生的阶段
    timestamp: datetime  # 动作发生时间

class GameState:
    """游戏状态类 - 包含当前牌桌所有可识别信息"""
    
    def __init__(self):
        # 牌桌基本信息
        self.table_id: str = ""  # 牌桌ID
        self.hand_id: str = ""  # 当前手牌ID
        self.timestamp: datetime = datetime.now()  # 状态更新时间
        
        # 游戏阶段信息
        self.street: Street = Street.PREFLOP  # 当前游戏阶段
        self.community_cards: List[str] = []  # 公共牌
        self.pot: int = 0  # 主底池大小
        self.side_pots: List[Tuple[int, Set[str]]] = []  # 边池(金额, 参与的玩家ID集合)
        
        # 玩家信息
        self.players: Dict[str, Player] = {}  # 所有玩家信息(包括已离桌但在本手牌中的玩家)
        self.seating: List[Optional[str]] = [None] * 6  # 座位安排(6人桌)
        self.button_position: int = 0  # 按钮位置(0-5)
        self.current_player: Optional[str] = None  # 当前应行动的玩家ID
        
        # 下注轮信息
        self.current_bet_round: int = 0  # 当前下注轮次(同一阶段内可能有多轮下注)
        self.bet_amount: int = 0  # 当前需要跟注的金额
        self.min_raise: int = 0  # 最小加注额度
        self.max_raise: int = 0  # 最大加注额度(通常为玩家剩余筹码)
        
        # 行动历史
        self.action_history: List[Action] = []  # 本手牌所有行动记录
        self.current_street_actions: List[Action] = []  # 当前阶段的行动记录
        
        # 牌局统计信息
        self.players_in_hand: Set[str] = set()  # 仍在牌局中的玩家ID
        self.players_all_in: Set[str] = set()  # 已全下的玩家ID
        self.players_folded: Set[str] = set()  # 已弃牌的玩家ID
        self.total_players: int = 6  # 牌桌总座位数
        self.active_players: int = 0  # 当前活跃玩家数(可行动的)
        
        # 历史信息(用于分析)
        self.preflop_raiser: Optional[str] = None  # 翻前最后加注者
        self.aggressor: Optional[str] = None  # 当前回合最后一个激进者(下注/加注者)
        self.last_raiser: Optional[str] = None  # 最后一个加注者
        
        # 牌桌配置
        self.small_blind: int = 0  # 小盲金额
        self.big_blind: int = 0  # 大盲金额
        self.min_buy_in: int = 0  # 最小买入
        self.max_buy_in: int = 0  # 最大买入
        
        # 时间信息
        self.time_bank: float = 0.0  # 剩余思考时间
        self.avg_action_time: float = 0.0  # 平均行动时间(所有玩家)
        
        # 游戏状态标志
        self.is_hero_turn: bool = False  # 是否是AI玩家的回合
        self.legal_actions: Set[ActionType] = set()  # 当前可执行的合法动作
        
    def get_hero(self) -> Optional[Player]:
        """获取AI玩家自身的信息"""
        # 在实际实现中，需要根据AI玩家的ID来获取
        # 这里假设AI玩家的ID为"hero"
        return self.players.get("hero")
    
    def get_opponents(self) -> List[Player]:
        """获取所有对手的信息"""
        return [player for player_id, player in self.players.items() 
                if player_id != "hero" and player.is_in_hand]
    
    def get_active_opponents(self) -> List[Player]:
        """获取所有活跃对手的信息"""
        return [player for player in self.get_opponents() if player.is_active]
    
    def get_players_by_position(self) -> List[Player]:
        """按位置顺序返回玩家列表(从按钮位置开始)"""
        result = []
        for i in range(6):
            player_id = self.seating[(self.button_position + i) % 6]
            if player_id and player_id in self.players:
                result.append(self.players[player_id])
        return result
    
    def get_relative_position(self, player_id: str) -> int:
        """获取玩家相对于按钮的位置(0=按钮, 1=小盲, 2=大盲, 3=枪口, 4=中间, 5=关煞)"""
        if player_id not in self.players:
            return -1
        
        player_index = self.seating.index(player_id)
        return (player_index - self.button_position) % 6
    
    def get_aggression_factor(self, player_id: str, street: Optional[Street] = None) -> float:
        """计算指定玩家在指定阶段的攻击性系数"""
        # 实现略 - 根据action_history计算
        pass
    
    def get_previous_actions(self, lookback: int = 10) -> List[Action]:
        """获取最近的历史动作"""
        return self.action_history[-lookback:] if self.action_history else []
    
    def get_players_in_hand_count(self) -> int:
        """获取仍在牌局中的玩家数量"""
        return len(self.players_in_hand)
    
    def get_pot_odds(self, call_amount: int) -> float:
        """计算当前底池赔率"""
        if call_amount <= 0:
            return 1.0
        return call_amount / (self.pot + call_amount)
    
    def get_effective_stack(self, player_id: str) -> int:
        """获取玩家的有效筹码量(与最短筹码玩家的最小值)"""
        if player_id not in self.players:
            return 0
        
        player_stack = self.players[player_id].stack
        min_opponent_stack = min(
            (p.stack for p in self.get_opponents() if p.is_in_hand),
            default=player_stack
        )
        return min(player_stack, min_opponent_stack)
    
    def get_stack_to_pot_ratio(self, player_id: str) -> float:
        """计算玩家的筹码量与底池比例(SPR)"""
        if player_id not in self.players or self.pot == 0:
            return float('inf')
        return self.players[player_id].stack / self.pot