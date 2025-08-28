import ddddocr
import io
from PIL import Image
import json

from models.game_state import GameState
from models.game_player import Player
from config.gg import SB, BB, ranks, process_config


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


class PokerOcr:

    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        self.image = None
        self.ocr_config = process_config()

    def fetch_state(self, image):
        self.image = image
        state = GameState()
        state.hand = self.__hand()
        state.board = self.__board()
        state.stage = 0 if len(state.board) == 0 else (len(state.board) - 2)
        state.position = self.__pos()
        state.pot = self.__ocr_amt(self.ocr_config['amount']['pool'])
        state.stack = self.__ocr_amt(self.ocr_config['amount']['balance'])
        state.call = self.__ocr_amt(self.ocr_config['amount']['call'])
        state.pls = self.__players(state.stage, state.position)
        return state

    def __ocr_txt(self, region):
        crop_image = self.image.crop(region)
        crop_image.save('image/cropped_image.png')
        image_bytes = io.BytesIO()
        crop_image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        result = self.ocr.classification(image_bytes)
        # result = self.ocr.classification(crop_image)
        return result

    def __ocr_amt(self, region):
        ocr_txt = self.__ocr_txt(region)
        ocr_amt = self.__convert_amt(ocr_txt)
        if ocr_amt == 0.0 and ocr_txt.__contains__('s'):
            region2 = (region[0]+5, region[1], region[0]+120, region[1]+31)
            ocr_txt2 = self.__ocr_txt(region2)
            return self.__convert_amt(ocr_txt2)
        return ocr_amt

    @staticmethod
    def __convert_amt(ocr_txt):
        if ocr_txt and '全押' not in ocr_txt:
            ocr_txt = ocr_txt.replace(" ", "")
            ocr_txt = ocr_txt.replace("o", "0")
            ocr_txt = ocr_txt.replace("O", "0")
            ocr_txt = ocr_txt.replace("z", "2")
            ocr_txt = ocr_txt.replace("Z", "2")
            length = len(ocr_txt)
            if length == 2:
                part1 = ocr_txt[1:]
                val = '{}.00'.format(part1)
            else:
                part1 = ocr_txt[1: length - 2]
                part2 = ocr_txt[length - 2: length]
                val = '{}.{}'.format(part1, part2)
            # print('amount:', ocr_txt)
            try:
                return float(val)
            except:
                return 0.0
        return 0.0

    def __ocr_card(self, region, suit_pos):
        ocr_txt = self.__ocr_txt(region)
        card_txt = self.__card(ocr_txt)
        if card_txt:
            color = self.image.getpixel(suit_pos)
            if match_color(self.ocr_config['suit']['s'], color, 20):
                return card_txt + 's'
            if match_color(self.ocr_config['suit']['h'], color, 20):
                return card_txt + 'h'
            if match_color(self.ocr_config['suit']['c'], color, 20):
                return card_txt + 'c'
            if match_color(self.ocr_config['suit']['d'], color, 20):
                return card_txt + 'd'
        return None

    @staticmethod
    def __card(ocr_txt):
        card_txt = None
        # print(ocr_txt)
        for c in ['A', 'K', 'k', 'Q', 'O', 'J', 'j', '10', '1o', '1O', '9', '8', '7', '6', '5', '4', '3', '2']:
            if c in ocr_txt:
                if c == '10' or c == '1O' or c == '1o':
                    card_txt = 'T'
                elif c == 'j':
                    card_txt = 'J'
                elif c == 'k':
                    card_txt = 'K'
                elif c == 'O':
                    card_txt = 'Q'
                else:
                    card_txt = c
                break
        return card_txt

    def __suit(self, suit_pos):
        color = self.image.getpixel(suit_pos)
        if match_color(self.ocr_config['suit']['s'], color, 50):
            return 's'
        if match_color(self.ocr_config['suit']['h'], color, 50):
            return 'h'
        if match_color(self.ocr_config['suit']['c'], color, 50):
            return 'c'
        if match_color(self.ocr_config['suit']['d'], color, 50):
            return 'd'
        return None

    def __players(self, stage, self_pos):
        pls = []
        w, h, bw, bh = self.ocr_config['player']['w_h'][0], self.ocr_config['player']['w_h'][1], self.ocr_config['player']['bet_w_h'][0], self.ocr_config['player']['bet_w_h'][1]
        bet_amount = 0
        for i in range(1, 6):
            if i in [1, 3, 4]:
                player_xy = eval("self.ocr_config['player']['{}_x1_y1']".format(i))
                x, y = player_xy[0], player_xy[1]
                player_bet_xy = eval("self.ocr_config['player']['{}_bet_x1_y1']".format(i))
                bx, by = player_bet_xy[0], player_bet_xy[1]
            elif i == 2:
                x, y = self.ocr_config['player']['1_x1_y1'][0], self.ocr_config['player']['4_x1_y1'][1]
                bx, by = self.ocr_config['player']['1_bet_x1_y1'][0], self.ocr_config['player']['4_bet_x1_y1'][1]
            else:
                x, y = self.ocr_config['player']['4_x1_y1'][0], self.ocr_config['player']['1_x1_y1'][1]
                bx, by = self.ocr_config['player']['4_bet_x1_y1'][0], self.ocr_config['player']['1_bet_x1_y1'][1]
            name = self.__ocr_txt((x, y, x+w, y+h))
            stack = self.__ocr_amt((x, y+h-5, x+w, y+h+h-5))
            amount = self.__ocr_amt((bx, by, bx+bw, by+bh))
            active = True if amount > 0 else contain_color(self.image.crop((x + 30, y + 5, x + w - 30, y + h - 10)),
                                                           self.ocr_config['player']['active_color'])
            position = (self_pos + i) % 6 if self_pos + i != 6 else 6

            if not active:
                action = 'fold'
            else:
                if stage == 0:
                    if position == 0 and amount == SB:
                        action = 'sb'
                    elif position == 1 and amount == BB:
                        action = 'bb'
                    else:
                        if amount == 0:
                            if position < self_pos:
                                action = 'fold'
                            else:
                                action = 'pending'
                        else:
                            if amount == bet_amount:
                                action = 'call'
                            else:
                                action = 'raise'
                                bet_amount = amount
                else:
                    if amount > 0:
                        if bet_amount == 0:
                            action = 'bet'      # 也可能是 call、raise
                            bet_amount = amount
                        else:
                            if amount > bet_amount:
                                action = 'raise'
                                bet_amount = amount
                            elif amount == bet_amount:
                                action = 'call'
                            else:
                                action = 'pending'
                    else:
                        if position < self_pos:
                            action = 'check'
                        else:
                            action = 'pending'
            pls.append(Player(name=name,
                              position=position,
                              stack=stack,
                              active=active,
                              action=action,
                              amount=amount))
        return sorted(pls, key=lambda p: p.position)

    def __hand(self):
        x1, y1 = self.ocr_config['hand']['card1_x1_y1'][0], self.ocr_config['hand']['card1_x1_y1'][1]
        x2, y2 = self.ocr_config['hand']['card2_x1_y1'][0], self.ocr_config['hand']['card2_x1_y1'][1]
        w, h = self.ocr_config['board']['card_w_h'][0], self.ocr_config['board']['card_w_h'][1]
        card1 = self.__ocr_card((x1, y1, x1+w, y1+h), self.ocr_config['hand']['suit1_x_y'])
        card2 = self.__ocr_card((x2, y2, x2+w, y2+h), self.ocr_config['hand']['suit2_x_y'])
        if card1 is None or card2 is None:
            two_card = self.__ocr_txt(self.ocr_config['hand']['region'])
            c1, c2 = two_card[0], two_card[1]
            if len(two_card) == 3:
                if c1 == "1":
                    c1 = self.__card(two_card[0] + two_card[1])
                    c2 = self.__card(two_card[2])
                else:
                    c1 = self.__card(two_card[0])
                    c2 = self.__card(two_card[1]+two_card[2])
            elif len(two_card) == 4:
                c1 = self.__card(two_card[0] + two_card[1])
                c2 = self.__card(two_card[2] + two_card[3])
            card1 = c1 + self.__suit(self.ocr_config['hand']['suit1_x_y'])
            card2 = c2 + self.__suit(self.ocr_config['hand']['suit2_x_y'])
        return ordered_hand([card1, card2])

    def __board(self):
        board = []
        x, y = self.ocr_config['board']['card1_x_y'][0], self.ocr_config['board']['card1_x_y'][1]
        w, h = self.ocr_config['board']['card_w_h'][0], self.ocr_config['board']['card_w_h'][1]

        for i in range(1, 6):
            x1 = x + (i - 1) * self.ocr_config['board']['distance']
            suit_pos = (self.ocr_config['board']['suit1_x_y'][0]+(i - 1) * self.ocr_config['board']['distance'], self.ocr_config['board']['suit1_x_y'][1])
            card = self.__ocr_card((x1, y, x1+w, y+h), suit_pos)
            if card:
                board.append(card)
            else:
                break
        return board

    def __pos(self):
        pos = -1
        for i in range(6):
            position = eval("self.ocr_config['btn']['x_y_{}']".format(i))
            color = self.image.getpixel(position)
            if match_color(self.ocr_config['btn']['color'], color, 50):
                pos = 6 - i
                break
        return pos


if __name__ == '__main__':
    ocr = PokerOcr()
    # for i1 in range(1, 43):
        # img1 = Image.open('../image/20250209133629/{}.jpg'.format(i))
        # img1 = Image.open('../image/{}.jpg'.format(i1))
        # state = ocr.fetch_state(img1)
        # print(i1, state.to_dict())

    # img1 = Image.open('../image/20250316172107.jpg')
    img1 = Image.open('../table_image.jpg')
    # img1 = Image.open('../image.png')
    state1 = ocr.fetch_state(img1)
    # print(state1.to_dict())

    # img2 = Image.open('../cropped_image2.jpg')
    # crop_image2 = img2.crop((0, 0, 118, 31))
    # ocr_res = ocr.ocr.classification(img2)
    # print(ocr_res)
