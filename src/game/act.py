import random
from enum import Enum
import math
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Action(Enum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    RAISE = 3

class Player:
    def __init__(self, name, initial_chips=100):
        self.name = name
        self.chips = initial_chips
        self.hand = []
        self.current_bet = 0
        self.is_active = True
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False
        self.action = None
        self.raised_amount = 0

    def place_bet(self, amount):
        if amount > self.chips:
            return False
        self.chips -= amount
        self.current_bet += amount
        return True

    def reset_bet(self):
        self.current_bet = 0
        self.action = None
        self.raised_amount = 0


    def clear_hand(self):
        self.hand = []

class GameLogic:
    def __init__(self):
        # 游戏设置
        self.players = [Player(f"玩家{i+1}") for i in range(6)]
        self.community_cards = []
        self.deck = []
        self.pot = 0
        self.current_bet = 0
        self.current_player_index = 0
        self.dealer_index = 0
        self.small_blind_index = 1
        self.big_blind_index = 2
        self.small_blind_amount = 1
        self.big_blind_amount = 2
        self.game_round = 0  # 0: 预翻牌, 1: 翻牌, 2: 转牌, 3: 河牌
        self.is_round_over = False
        self.is_game_over = False

    def start_new_game(self):
        logger.info("开始新游戏")
        # 重置游戏状态
        self.pot = 0
        self.current_bet = 0
        self.community_cards = []
        self.game_round = 0
        self.is_round_over = False
        self.is_game_over = False

        # 重置玩家状态
        for player in self.players:
            player.reset_bet()
            player.clear_hand()
            player.is_active = True
            player.is_dealer = False
            player.is_small_blind = False
            player.is_big_blind = False

        # 生成新牌堆
        self.create_deck()

        # 确定庄家、小盲注和大盲注位置
        self.dealer_index = (self.dealer_index + 1) % 6
        self.small_blind_index = (self.dealer_index + 1) % 6
        self.big_blind_index = (self.dealer_index + 2) % 6

        self.players[self.dealer_index].is_dealer = True
        self.players[self.small_blind_index].is_small_blind = True
        self.players[self.big_blind_index].is_big_blind = True

        # 收取盲注
        self.collect_blinds()

        # 设置当前玩家（大盲注的下一位）
        self.current_player_index = (self.big_blind_index + 1) % 6
        logger.info(f"当前玩家索引: {self.current_player_index}, 玩家名称: {self.players[self.current_player_index].name}")
        while not self.players[self.current_player_index].is_active:
            self.current_player_index = (self.current_player_index + 1) % 6

    def create_deck(self):
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = [(rank, suit) for suit in suits for rank in ranks]
        random.shuffle(self.deck)

    def collect_blinds(self):
        # 小盲注
        small_blind_player = self.players[self.small_blind_index]
        small_blind_player.place_bet(self.small_blind_amount)
        self.pot += self.small_blind_amount
        self.current_bet = self.small_blind_amount

        # 大盲注
        big_blind_player = self.players[self.big_blind_index]
        big_blind_player.place_bet(self.big_blind_amount)
        self.pot += self.big_blind_amount
        self.current_bet = self.big_blind_amount

    def deal_hole_cards(self):
        for _ in range(2):  # 每个玩家发两张牌
            for i, player in enumerate(self.players):
                if player.is_active:
                    card = self.deck.pop()
                    player.hand.append(card)

    def player_action(self, action, raise_amount=None):
        current_player = self.players[self.current_player_index]
        result = {'success': True, 'message': ''}

        if action == Action.FOLD:
            current_player.is_active = False
            result['message'] = f"{current_player.name} 弃牌\n"

        elif action == Action.CHECK:
            if current_player.current_bet < self.current_bet:
                result['success'] = False
                result['message'] = "当前有下注，不能过牌"
            else:
                result['message'] = f"{current_player.name} 过牌\n"

        elif action == Action.CALL:
            amount_to_call = self.current_bet - current_player.current_bet
            if current_player.place_bet(amount_to_call):
                self.pot += amount_to_call
                result['message'] = f"{current_player.name} 跟注 {amount_to_call}\n"
            else:
                result['success'] = False
                result['message'] = "筹码不足"

        elif action == Action.RAISE:
            # 计算需要跟注的金额
            amount_to_call = self.current_bet - current_player.current_bet
            
            # 如果没有提供加注金额，默认使用当前下注的两倍
            if raise_amount is None:
                raise_amount = self.current_bet * 2
            
            # 总下注金额 = 已下注金额 + 跟注金额 + 加注金额
            total_bet = current_player.current_bet + amount_to_call + raise_amount

            if current_player.place_bet(amount_to_call + raise_amount):
                self.pot += amount_to_call + raise_amount
                self.current_bet = total_bet
                current_player.raised_amount = raise_amount
                result['message'] = f"{current_player.name} 加注到 {total_bet}\n"
            else:
                result['success'] = False
                result['message'] = "筹码不足"

        return result

    def move_to_next_player(self):
        logger.info(f"移动到下一位玩家，当前玩家: {self.players[self.current_player_index].name}")
        # 检查是否所有玩家都已行动
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) == 1:
            # 只剩一个玩家，直接获胜
            return {'end_hand': True, 'winner': active_players[0], 'end_round': False}

        # 找到下一个活跃玩家
        next_index = (self.current_player_index + 1) % 6
        while not self.players[next_index].is_active:
            next_index = (next_index + 1) % 6

        # 检查是否完成一轮下注
        # 在预翻牌阶段，起始玩家是大盲注的下一位
        if self.game_round == 0:
            start_player_index = (self.big_blind_index + 1) % 6
            while not self.players[start_player_index].is_active:
                start_player_index = (start_player_index + 1) % 6
        else:
            # 翻牌后阶段，起始玩家是庄家的下一位
            start_player_index = (self.dealer_index + 1) % 6
            while not self.players[start_player_index].is_active:
                start_player_index = (start_player_index + 1) % 6

        # 检查是否所有活跃玩家都已行动且下注相等。
        all_acted = True
        all_bet_equal = True
        current_bet = self.current_bet
        
        for player in active_players:
            # 检查是否有玩家还未行动（下注小于当前最高下注）
            if player.current_bet < current_bet:
                all_acted = False
                all_bet_equal = False
                break

        # 如果回到了起始玩家且所有玩家都已行动，则结束本轮
        if next_index == start_player_index and all_acted:
            return {'end_hand': False, 'end_round': True, 'next_index': next_index}

        self.current_player_index = next_index
        return {'end_hand': False, 'end_round': False, 'next_index': next_index}

    def end_betting_round(self):
        logger.info(f"结束下注轮，当前轮次: {self.game_round}")
        # 重置当前下注和玩家行动状态
        self.current_bet = 0
        for player in self.players:
            player.reset_bet()
            player.action = None  # 重置玩家行动状态，确保下一轮正确判断

        result = {'showdown': False, 'community_cards_added': False}

        if self.game_round == 0:  # 预翻牌后
            # 翻牌 - 发三张公共牌
            self.deal_community_cards(3)
            self.game_round = 1
            result['community_cards_added'] = True
        elif self.game_round == 1:  # 翻牌后
            # 转牌 - 发一张公共牌
            self.deal_community_cards(1)
            self.game_round = 2
            result['community_cards_added'] = True
        elif self.game_round == 2:  # 转牌后
            # 河牌 - 发一张公共牌
            self.deal_community_cards(1)
            self.game_round = 3
            result['community_cards_added'] = True
        elif self.game_round == 3:  # 河牌后
            # 摊牌，决定获胜者
            result['showdown'] = True

        # 根据游戏阶段设置当前玩家
        if not result['showdown']:
            # 翻牌后所有阶段都从庄家的下一位开始
            start_index = (self.dealer_index + 1) % 6

            # 找到下一个活跃玩家
            self.current_player_index = start_index
            found_active = False
            while True:
                if self.players[self.current_player_index].is_active:
                    found_active = True
                    break
                self.current_player_index = (self.current_player_index + 1) % 6
                if self.current_player_index == start_index:
                    break

            # 如果没有活跃玩家，结束游戏
            if not found_active:
                self.is_game_over = True

        return result

    def deal_community_cards(self, count):
        for _ in range(count):
            card = self.deck.pop()
            self.community_cards.append(card)

    def determine_winner(self):
        logger.info("判定获胜者")
        # 暂时实现一个简单的获胜者判定，避免导入问题
        active_players = [p for p in self.players if p.is_active]
        logger.info(f"当前活跃玩家: {[p.name for p in active_players]}")
        if len(active_players) == 1:
            logger.info(f"只有一位活跃玩家，获胜者: {active_players[0].name}")
            return {'message': f"{active_players[0].name} 获胜！赢得 {self.pot} 筹码（唯一剩余玩家）\n"}
        else:
            # 简单地选择第一个活跃玩家作为获胜者
            # 实际应用中应该使用真正的牌型计算
            winner = active_players[0]
            logger.info(f"选择第一个活跃玩家作为获胜者: {winner.name}")
            return {'message': f"{winner.name} 获胜！赢得 {self.pot} 筹码\n"}

    def end_hand(self, winner):
        # 注意：这里的winner参数实际上是从determine_winner方法返回的消息字典
        # 我们需要从players列表中找到实际的获胜者对象
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) == 1:
            actual_winner = active_players[0]
        else:
            actual_winner = active_players[0]

        logger.info(f"结束手牌，获胜者: {actual_winner.name}，底池大小: {self.pot}")
        logger.info(f"添加底池筹码前 {actual_winner.name} 的筹码: {actual_winner.chips}")
        actual_winner.chips += self.pot
        logger.info(f"添加底池筹码后 {actual_winner.name} 的筹码: {actual_winner.chips}")
        logger.info(f"{actual_winner.name} 赢得 {self.pot} 筹码，当前筹码: {actual_winner.chips}")
        return {'message': f"{actual_winner.name} 获胜！赢得 {self.pot} 筹码\n"}