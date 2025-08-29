import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # 禁用生成__pycache__目录

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

# 小盲注和大盲注
SB = 0.01
BB = 0.02
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suits = ['s', 'h', 'c', 'd']


# 当前运行环境下桌面区别
# CUR_TABLE_REGION = (9, 30, 860, 645)
CUR_TABLE_REGION = (129, 58, 1335, 919)

# BASE基于(1440, 900)分辨率截取的图像
BASE_TABLE_REGION = (129, 58, 1335, 919)
WIN_BASE = {
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
        'call': (1047, 861, 1138, 889)
    },
    'action': {
        'color': (153, 56, 50),
        'fold': (937, 860),
        'call': (1096, 860),
        'raise': (1252, 860),
        'add': (1301, 787)
    }
}

def process_config(data=WIN_BASE):
    if isinstance(data, tuple):
        return new_loc(data)
    elif isinstance(data, dict):
        return {k: new_wh(v) if 'w_h' in k else process_config(v) for k, v in data.items()}
    else:
        return new_loc(data)

def new_wh(wh):
    w, h = wh[0], wh[1]
    x_rate = (CUR_TABLE_REGION[2]-CUR_TABLE_REGION[0]) / (BASE_TABLE_REGION[2] - BASE_TABLE_REGION[0])
    y_rate = (CUR_TABLE_REGION[3]-CUR_TABLE_REGION[1]) / (BASE_TABLE_REGION[3] - BASE_TABLE_REGION[1])
    return int(w * x_rate), int(h * y_rate)


def new_loc(loc):
    x_rate = (CUR_TABLE_REGION[2] - CUR_TABLE_REGION[0]) / (BASE_TABLE_REGION[2] - BASE_TABLE_REGION[0])
    y_rate = (CUR_TABLE_REGION[3] - CUR_TABLE_REGION[1]) / (BASE_TABLE_REGION[3] - BASE_TABLE_REGION[1])
    x_base_offset, y_base_offset = BASE_TABLE_REGION[0], BASE_TABLE_REGION[1]
    x_cur_offset, y_cur_offset = CUR_TABLE_REGION[0], CUR_TABLE_REGION[1]

    if isinstance(loc, (list, tuple)):
        if len(loc) == 2:
            x, y = loc[0], loc[1]
            return (int((x - x_base_offset) * x_rate) + x_cur_offset,
                    int((y - y_base_offset) * y_rate) + y_cur_offset)
        elif len(loc) == 3:
            return loc
        elif len(loc) == 4:
            x1, y1, x2, y2 = loc[0], loc[1], loc[2], loc[3]
            return (int((x1 - x_base_offset) * x_rate) + x_cur_offset,
                    int((y1 - y_base_offset) * y_rate) + y_cur_offset,
                    int((x2 - x_base_offset) * x_rate) + x_cur_offset,
                    int((y2 - y_base_offset) * y_rate) + y_cur_offset)
    elif isinstance(loc, (int, float)):
        return int((loc - x_base_offset) * x_rate) + x_cur_offset
    else:
        return loc
