# 需要远程到游戏桌面, 远程桌面分辩设置为：1440*900
# 游戏窗口最大化，牌需要设置为4色

# 桌面信息定位
# 位置： POSITION_XXX = (x,y) 即left和top
# 区域：REGION_XXX = (x,y,w,h)
# 颜色：COLOR_XXX = (r,g,b)
# 定位：LOCATION_XXX = (position, color)


# 识别游戏窗口标题
WIN_TITLE = "192.168.0.113 - 远程桌面连接"
# WIN_TITLE = "192.168.1.200 - 远程桌面连接"
CUR_TABLE_PIXEL = (850, 614)
CUR_WIN_OFFSET = (8, 31)


# 基准的牌桌截图。基于(1440, 900)分辨率截取的像素
BASE_TABLE_PIXEL = (1208, 860)
BASE_WIN_OFFSET = (129, 58)

# 当前运行的桌面. 更换新的桌面运行时，只需要定位两个值：1. 牌桌的像素。 2. 牌桌相对于截图的偏移量
# CUR_TABLE_PIXEL = (1208, 860)
# CUR_WIN_OFFSET = (129, 58)

SB = 0.01
BB = 0.02

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suits = ['s', 'h', 'c', 'd']

WIN_1440_900 = {
    'hand': {
        'region': (645, 690, 800, 735),
        'card1_x1_y1': (645, 690),
        'suit1_x_y': (676, 751),
        'card2_x1_y1': (718, 690),
        'suit2_x_y': (737, 746)
    },
    'board': {
        'card1_x_y': (486, 408),
        'suit1_x_y': (546, 486),
        'distance': 105,
        'card_w_h': (45, 35)
    },
    'suit': {
        's': (0, 0, 0),
        'h': (202, 23, 27),
        'c': (29, 126, 45),
        'd': (1, 30, 196)
    },
    'player': {
        '1_x1_y1': (185, 660),
        '1_bet_x1_y1': (350, 575),
        '3_x1_y1': (666, 225),
        '3_bet_x1_y1': (660, 315),
        '4_x1_y1': (1090, 310),
        '4_bet_x1_y1': (945, 360),
        'w_h': (175, 31),
        'bet_w_h': (175, 35),
        'active_color': (253, 253, 253)
    },
    'btn': {
        'color': (239, 195, 44),
        'x_y_0': (648, 657),
        'x_y_1': (392, 634),
        'x_y_2': (392, 353),
        'x_y_3': (672, 303),
        'x_y_4': (1057, 353),
        'x_y_5': (1057, 634)
    },
    'amount': {
        'pool': (729, 368, 817, 402),
        'balance': (658, 832, 812, 872),
        'call': (1047, 856, 1138, 886)
    },
    'action': {
        'color': (171, 67, 63),
        'fold': (937, 860),
        'call': (1096, 860),
        'raise': (1252, 860),
        'add': (1301, 787)
    }
}


#  ===== 手牌及公共牌 =====
# 4种花色的颜色值。黑桃（Spade）红桃（Heart）梅花（Club）方块（Diamond）
SUIT_COLOR = ((0, 0, 0), (202, 23, 27), (29, 126, 45), (1, 30, 196))
# 单个牌要截取的宽度和高度
CARD_WIDTH, CARD_HEIGHT = 45, 55
# 第1张牌识别区域、花色位置
REGION_CARD_1 = (650, 690, CARD_WIDTH, CARD_HEIGHT)
POSITION_SUIT_1 = (676, 751)
# 第2张牌识别区域、花色位置
REGION_CARD_2 = (718, 690, CARD_WIDTH, CARD_HEIGHT)
POSITION_SUIT_2 = (737, 746)
# 第3张牌识别区域、花色位置
REGION_CARD_3 = (486, 408, CARD_WIDTH, CARD_HEIGHT)
POSITION_SUIT_3 = (546, 486)
# 公共牌之间的间隔
PUB_CARD_SPACE_X = 100

# ===== 底池金额 =====
# 底池区域（l,t,w,h)
REGION_POOL = (729, 368, 88, 30)


# ===== 玩家信息ocr识别，包括名称、金额、位置 =====
# 读取玩家信息的区域
PLAYER_WIDTH, PLAYER_HEIGHT = 135, 31
REGION_PLAYER_1 = (194, 657, PLAYER_WIDTH, PLAYER_HEIGHT)
REGION_PLAYER_2 = (233, 304, PLAYER_WIDTH, PLAYER_HEIGHT)
REGION_PLAYER_3 = (666, 230, PLAYER_WIDTH, PLAYER_HEIGHT)
REGION_PLAYER_4 = (1099, 309, PLAYER_WIDTH, PLAYER_HEIGHT)
REGION_PLAYER_5 = (1137, 658, PLAYER_WIDTH, PLAYER_HEIGHT)

PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT = 175, 61
REGION_PLAYER_BET_1 = (350, 575, PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT)
REGION_PLAYER_BET_2 = (350, 355, PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT)
REGION_PLAYER_BET_3 = (660, 315, PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT)
REGION_PLAYER_BET_4 = (945, 355, PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT)
REGION_PLAYER_BET_5 = (945, 575, PLAYER_BET_WIDTH, PLAYER_BET_HEIGHT)

# 识别btn所在位置
COLOR_BOTTOM = (239, 195, 44)   # D标记颜色
POSITION_BOTTOM_0 = (648, 657)  # 我
POSITION_BOTTOM_1 = (392, 634)  # 左下
POSITION_BOTTOM_2 = (392, 353)  # 左上
POSITION_BOTTOM_3 = (672, 303)  # 上
POSITION_BOTTOM_4 = (1057, 353)  # 右上
POSITION_BOTTOM_5 = (1057, 634)  # 右下


#  ===== 操作判断 =====

# 判断当前牌桌是否需要采取行动。通过手牌位置的背景颜色来判断
POSITION_READY = (701, 724)
COLOR_READY = (239, 239, 239)

# 按钮颜色。 fold、call、raise操作按钮的位置
COLOR_BUTTON = (171, 67, 63)
POSITION_BUTTON_FOLD = (937, 860)
POSITION_BUTTON_CALL = (1096, 860)
POSITION_BUTTON_RAISE = (1252, 860)

POSITION_BUTTON_ADD_RAISE = (1301, 787)

# ocr跟注金额
REGION_CALL_AMOUNT = (1047, 856, 91, 30)

