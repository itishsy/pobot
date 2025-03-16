import json
from typing import Any, Callable
from poker.config import *


def process_json_values(
    data: Any,
    processor: Callable[[Any], Any],
    process_keys: bool = False
) -> Any:
    """
    递归处理JSON对象的所有值
    :param data: 原始数据（支持dict/list/基础类型）
    :param processor: 值处理函数
    :param process_keys: 是否处理字典键
    :return: 处理后的新数据
    """
    if isinstance(data, dict):
        return {
            (processor(k) if process_keys else k): process_json_values(v, processor)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [process_json_values(item, processor) for item in data]
    else:
        return processor(data)


def new_loc(loc):
    x_fbl_rate, y_fbl_rate = CUR_FBL[0] / BASE_FBL[0], CUR_FBL[1] / BASE_FBL[1]
    x_base_offset, y_base_offset = BASE_WIN_OFFSET[0], BASE_WIN_OFFSET[1]
    x_cur_offset, y_cur_offset = CUR_WIN_OFFSET[0], CUR_WIN_OFFSET[1]
    if len(loc) == 2:
        x, y = loc[0], loc[1]
        return (int((x - x_base_offset) * x_fbl_rate) + x_cur_offset,
                int((y - y_base_offset) * y_fbl_rate) + y_cur_offset)
    elif len(loc) == 4:
        x1, y1, x2, y2 = loc[0], loc[1], loc[2], loc[3]
        return (int((x1 - x_base_offset) * x_fbl_rate) + x_cur_offset,
                int((y1 - y_base_offset) * y_fbl_rate) + y_cur_offset,
                int((x2 - x_base_offset) * x_fbl_rate) + x_cur_offset,
                int((y2 - y_base_offset) * y_fbl_rate) + y_cur_offset)
    elif len(loc) == 4:
        return int((loc - x_base_offset) * x_fbl_rate) + x_cur_offset
    else:
        return loc


def get_ocr_config():
    base_config = WIN_1440_900
    processed = process_json_values(base_config, new_loc)
    obj = json.dumps(processed, indent=2)
    return obj


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
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    if ranks.index(rank1) > ranks.index(rank2):
        return hand
    else:
        return [hand[1], hand[0]]
