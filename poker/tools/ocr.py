import ddddocr
import io
from PIL import Image

from poker.tools.util import match_color, contain_color, ordered_hand
from poker.models.game import State, Player
from poker.config import current_ocr_config


class PokerOcr:

    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        self.image = None

        hand, board, suit, player, btn, amount = current_ocr_config()

        # region=(x1,y1,x2,y2)，其中x1,y1为区域左上角,x2,y2为区域右下角; 用wh来表示为(x1,y1,x1+w,y1+h)
        # 7张牌。
        self.hand_region = hand.get('region')
        self.hand1_pos = hand.get('card1_x1_y1')  # (645, 690)
        self.hand1_suit_x_y = hand.get('')  # (676, 751)
        self.hand2_pos = hand.get('')  # (718, 690)
        self.hand2_suit_x_y = hand.get('')  # (737, 746)
        self.board_x_y = board.get('')  # (486, 408)
        self.board_suit_x_y = board.get('')  # (546, 486)
        self.board_distance = board.get('')  # 105
        self.card_w_h = board.get('')  # (45, 35)
        self.suit_color = suit.get('')  # ((0, 0, 0), (202, 23, 27), (29, 126, 45), (1, 30, 196))   # 4种花色的rgb

        # 5个玩家: 名称、金额、打出金额。只需定位134,25可计算出来
        self.player1_x1_y1 = (185, 660)
        self.player3_x1_y1 = (666, 225)
        self.player4_x1_y1 = (1090, 310)
        self.player_w_h = (175, 31)
        self.player1_bet_x1_y1 = (350, 575)
        self.player3_bet_x1_y1 = (660, 315)
        self.player4_bet_x1_y1 = (945, 360)
        self.player_bet_w_h = (175, 35)
        self.player_active_color = (253, 253, 253)

        # 底池、位置
        self.pool_region = (729, 368, 817, 398)
        self.btn_color = (239, 195, 44)  # D标记颜色
        self.btn_x_y_0 = (648, 657)  # 我
        self.btn_x_y_1 = (392, 634)  # 左下
        self.btn_x_y_2 = (392, 353)  # 左上
        self.btn_x_y_3 = (672, 303)  # 上
        self.btn_x_y_4 = (1057, 353)  # 右上
        self.btn_x_y_5 = (1057, 634)  # 右下

        # 余额、跟注金额
        self.call_amount_region = (1047, 856, 1138, 886)
        self.balance_region = (658, 832, 812, 872)

    def fetch_state(self, image):
        self.image = image
        stage = State()
        stage.hand = self.__hand()
        stage.board = self.__board()
        stage.stage = 0 if len(stage.board) == 0 else len(stage.board) - 2
        stage.position = self.__pos()
        stage.pot = self.__ocr_amt(self.pool_region)
        stage.stack = self.__ocr_amt(self.balance_region)
        stage.call = self.__ocr_amt(self.call_amount_region)
        stage.players = self.__players()
        return stage

    def __ocr_txt(self, region):
        crop_image = self.image.crop(region)
        crop_image.save('c:\\Huangsy\\sourcecode\\pobot\\poker\\cropped_image.png')
        image_bytes = io.BytesIO()
        crop_image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        result = self.ocr.classification(image_bytes)
        # result = self.ocr.classification(crop_image)
        return result

    def __ocr_amt(self, region):
        ocr_txt = self.__ocr_txt(region)
        # print(ocr_txt)
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
        if card_txt:
            color = self.image.getpixel(suit_pos)
            if match_color(self.suit_color[0], color, 20):
                return card_txt + 's'
            if match_color(self.suit_color[1], color, 20):
                return card_txt + 'h'
            if match_color(self.suit_color[2], color, 20):
                return card_txt + 'c'
            if match_color(self.suit_color[3], color, 20):
                return card_txt + 'd'
        return None

    def __card(self, ocr_txt):
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
        if match_color(self.suit_color[0], color, 50):
            return 's'
        if match_color(self.suit_color[1], color, 50):
            return 'h'
        if match_color(self.suit_color[2], color, 50):
            return 'c'
        if match_color(self.suit_color[3], color, 50):
            return 'd'
        return None

    def __players(self):
        pls = []
        w, h, bw, bh = self.player_w_h[0], self.player_w_h[1], self.player_bet_w_h[0], self.player_bet_w_h[1]
        self_pos = self.__pos()
        for i in range(1, 6):
            if i in [1, 3, 4]:
                x, y = eval('self.player{}_x1_y1[0]'.format(i)), eval('self.player{}_x1_y1[1]'.format(i))
                bx, by = eval('self.player{}_bet_x1_y1[0]'.format(i)), eval('self.player{}_bet_x1_y1[1]'.format(i))
            elif i == 2:
                x, y = self.player1_x1_y1[0], self.player4_x1_y1[1]
                bx, by = self.player1_bet_x1_y1[0], self.player4_bet_x1_y1[1]
            else:
                x, y = self.player4_x1_y1[0], self.player1_x1_y1[1]
                bx, by = self.player4_bet_x1_y1[0], self.player1_bet_x1_y1[1]
            name = self.__ocr_txt((x, y, x+w, y+h))
            stack = self.__ocr_amt((x, y+h-5, x+w, y+h+h-5))
            amount = self.__ocr_amt((bx, by, bx+bw, by+bh))
            if amount > 0:
                active = 1
            else:
                active = contain_color(self.image.crop((x + 30, y + 5, x + w - 30, y + h - 10)),
                                       self.player_active_color)
            position = (self_pos + i) % 6 if self_pos + i != 6 else 6
            if active:
                if amount > 0:
                    action = 'bet'
                else:
                    if position > self_pos:
                        action = 'pending'
                    else:
                        action = 'check'
            else:
                action = 'fold'
            pls.append(Player(name=name,
                              position=position,
                              stack=stack,
                              active=1 if active else 0,
                              action=action,
                              amount=amount))
        return pls

    def __hand(self):
        x1, y1 = self.hand1_pos[0], self.hand1_pos[1]
        x2, y2 = self.hand2_pos[0], self.hand2_pos[1]
        w, h = self.card_w_h[0], self.card_w_h[1]
        card1 = self.__ocr_card((x1, y1, x1+w, y1+h), self.hand1_suit_x_y)
        card2 = self.__ocr_card((x2, y2, x2+w, y2+h), self.hand2_suit_x_y)
        if card1 is None or card2 is None:
            two_card = self.__ocr_txt(self.hand_region)
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
            card1 = c1 + self.__suit(self.hand1_suit_x_y)
            card2 = c2 + self.__suit(self.hand2_suit_x_y)
        return ordered_hand([card1, card2])

    def __board(self):
        board = []
        x, y = self.board_x_y[0], self.board_x_y[1]
        w, h = self.card_w_h[0], self.card_w_h[1]

        for i in range(1, 6):
            x1 = x + (i - 1) * self.board_distance
            suit_pos = (self.board_suit_x_y[0]+(i - 1) * self.board_distance, self.board_suit_x_y[1])
            card = self.__ocr_card((x1, y, x1+w, y+h), suit_pos)
            if card:
                board.append(card)
            else:
                break
        return board

    def __pos(self):
        pos = -1
        for i in range(6):
            position = eval('self.btn_x_y_{}'.format(i))
            color = self.image.getpixel(position)
            if match_color(self.btn_color, color, 50):
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

    img1 = Image.open('../image/None.jpg')
    state = ocr.fetch_state(img1)
    print(state.to_dict())

    # img2 = Image.open('../cropped_image2.jpg')
    # crop_image2 = img2.crop((0, 0, 118, 31))
    # ocr_res = ocr.ocr.classification(img2)
    # print(ocr_res)
