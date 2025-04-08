from poker.config import *


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
    x_rate = (CUR_TABLE_REGION[2]-CUR_TABLE_REGION[0]) / (BASE_TABLE_REGION[2] - BASE_TABLE_REGION[0])
    y_rate = (CUR_TABLE_REGION[3]-CUR_TABLE_REGION[1]) / (BASE_TABLE_REGION[3] - BASE_TABLE_REGION[1])
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


def match_color(color1, color2, diff=100):
    return (abs(color1[0] - color2[0]) < diff and
            abs(color1[1] - color2[1]) < diff and
            abs(color1[2] - color2[2]) < diff)


def contain_color(image, color):
    width, height = image.size
    # 遍历所有像素
    for x in range(width):
        for y in range(height):
            current_rgb = image.getpixel((x, y))
            if current_rgb == color:
                return True
    return False


def ordered_hand(hand):
    rank1 = hand[0][:-1]
    rank2 = hand[1][:-1]
    if ranks.index(rank1) > ranks.index(rank2):
        return hand
    else:
        return [hand[1], hand[0]]


def cur_table_x1y1(image):
    for i in range(200):
        for j in range(100):
            if match_color(image.getpixel((i, j)), COLOR_TABLE_X1Y1, 50):
                return i, j


def cur_table_x2y2(image):
    for i in range(200):
        for j in range(100):
            x, y = image.width - i - 1, image.height - j - 1
            if match_color(image.getpixel((x, y)), COLOR_TABLE_X2Y2, 50):
                return x, y
