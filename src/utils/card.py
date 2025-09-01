from collections import Counter
from itertools import combinations

# 牌型强度常量
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

# 牌面大小映射
RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

def evaluate_hand(cards):
    # 确保我们有5张牌用于评估
    if len(cards) < 5:
        return (HIGH_CARD, [])

    # 分离牌面和花色
    ranks = []
    suits = []
    for card in cards:
        if card.startswith('10'):
            ranks.append('10')
            suits.append(card[2:])
        else:
            ranks.append(card[0])
            suits.append(card[1:])

    # 转换牌面为数值
    rank_values = [RANK_VALUES[rank] for rank in ranks]
    sorted_ranks = sorted(rank_values, reverse=True)

    # 检查是否是同花顺
    is_flush = all(suit == suits[0] for suit in suits)
    is_straight = (max(rank_values) - min(rank_values) == 4 and
                   len(set(rank_values)) == 5)

    # 特殊情况：A-2-3-4-5的顺子
    if sorted_ranks == [14, 5, 4, 3, 2]:
        is_straight = True
        sorted_ranks = [5, 4, 3, 2, 1]  # 调整A为最低，用1表示

    if is_flush and is_straight:
        # 检查是否是皇家同花顺
        if sorted_ranks[0] == 14:
            return (ROYAL_FLUSH, sorted_ranks)
        return (STRAIGHT_FLUSH, sorted_ranks)

    # 检查是否是四条
    rank_counts = Counter(rank_values)
    if 4 in rank_counts.values():
        four_rank = [rank for rank, count in rank_counts.items() if count == 4][0]
        kicker = [rank for rank in sorted_ranks if rank != four_rank][0]
        return (FOUR_OF_A_KIND, [four_rank, kicker])

    # 检查是否是葫芦
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        three_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
        pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
        return (FULL_HOUSE, [three_rank, pair_rank])

    # 检查是否是同花
    if is_flush:
        return (FLUSH, sorted_ranks)

    # 检查是否是顺子
    if is_straight:
        return (STRAIGHT, sorted_ranks)

    # 检查是否是三条
    if 3 in rank_counts.values():
        three_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
        kickers = sorted([rank for rank in sorted_ranks if rank != three_rank], reverse=True)
        return (THREE_OF_A_KIND, [three_rank] + kickers)

    # 检查是否是两对
    if list(rank_counts.values()).count(2) == 2:
        pairs = sorted([rank for rank, count in rank_counts.items() if count == 2], reverse=True)
        kicker = [rank for rank in sorted_ranks if rank not in pairs][0]
        return (TWO_PAIR, pairs + [kicker])

    # 检查是否是一对
    if 2 in rank_counts.values():
        pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
        kickers = sorted([rank for rank in sorted_ranks if rank != pair_rank], reverse=True)
        return (ONE_PAIR, [pair_rank] + kickers)

    # 高牌
    return (HIGH_CARD, sorted_ranks)

def get_best_hand(hole_cards, community_cards):
    # 组合玩家手牌和公共牌
    all_cards = hole_cards + community_cards
    best_score = (HIGH_CARD, [])
    best_details = []

    # 生成所有可能的5张牌组合
    for combination in combinations(all_cards, 5):
        score, ranks = evaluate_hand(combination)
        if (score > best_score[0] or
            (score == best_score[0] and ranks > best_score[1])):
            best_score = (score, ranks)
            best_details = ranks

    return best_score[0], best_details


def compare_hands(hand1, hand2, community_cards):
    # 获取每个玩家的最佳手牌分数和详细信息
    player1_score, player1_details = get_best_hand(hand1, community_cards)
    player2_score, player2_details = get_best_hand(hand2, community_cards)

    # 比较牌型大小
    if player1_score > player2_score:
        return 1
    elif player1_score < player2_score:
        return -1
    else:
        # 牌型相同，比较详细信息
        if player1_details > player2_details:
            return 1
        elif player1_details < player2_details:
            return -1
        else:
            # 完全相同的牌型，比较剩余的牌（kickers）
            # 获取所有牌的组合
            player1_all_cards = player1.hand + community_cards
            player2_all_cards = player2.hand + community_cards

            # 评估所有可能的5张牌组合
            player1_best = (0, [])
            for combo in combinations(player1_all_cards, 5):
                score, details = evaluate_hand(combo)
                if (score > player1_best[0] or 
                    (score == player1_best[0] and details > player1_best[1])):
                    player1_best = (score, details)

            player2_best = (0, [])
            for combo in combinations(player2_all_cards, 5):
                score, details = evaluate_hand(combo)
                if (score > player2_best[0] or 
                    (score == player2_best[0] and details > player2_best[1])):
                    player2_best = (score, details)

            # 比较最终的详细信息
            if player1_best[1] > player2_best[1]:
                return 1
            elif player1_best[1] < player2_best[1]:
                return -1
            else:
                return 0

