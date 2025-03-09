def match_color(color1, color2, diff=100):
    return (abs(color1[0] - color2[0]) < diff and
            abs(color1[1] - color2[1]) < diff and
            abs(color1[2] - color2[2]) < diff)


def ordered_hand(hand):
    rank1 = hand[0][:-1]
    rank2 = hand[1][:-1]
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    if ranks.index(rank1) > ranks.index(rank2):
        return hand
    else:
        return [hand[1], hand[0]]
