from poker.config import *


def process_values(data):
    if isinstance(data, tuple):
        return new_loc(data)
    elif isinstance(data, dict):
        return {k: process_values(v) for k, v in data.items()}
    else:
        return new_loc(data)


def new_loc(loc):
    x_fbl_rate, y_fbl_rate = CUR_FBL[0] / BASE_FBL[0], CUR_FBL[1] / BASE_FBL[1]
    x_base_offset, y_base_offset = BASE_WIN_OFFSET[0], BASE_WIN_OFFSET[1]
    x_cur_offset, y_cur_offset = CUR_WIN_OFFSET[0], CUR_WIN_OFFSET[1]
    
    if isinstance(loc, (list, tuple)):
        if len(loc) == 2:
            x, y = loc[0], loc[1]
            return (int((x - x_base_offset) * x_fbl_rate) + x_cur_offset,
                    int((y - y_base_offset) * y_fbl_rate) + y_cur_offset)
        elif len(loc) == 3:
            return loc
        elif len(loc) == 4:
            x1, y1, x2, y2 = loc[0], loc[1], loc[2], loc[3]
            return (int((x1 - x_base_offset) * x_fbl_rate) + x_cur_offset,
                    int((y1 - y_base_offset) * y_fbl_rate) + y_cur_offset,
                    int((x2 - x_base_offset) * x_fbl_rate) + x_cur_offset,
                    int((y2 - y_base_offset) * y_fbl_rate) + y_cur_offset)
    elif isinstance(loc, (int, float)):
        return int((loc - x_base_offset) * x_fbl_rate) + x_cur_offset
    else:
        return loc


def get_ocr_config():
    return process_values(WIN_1440_900)


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
