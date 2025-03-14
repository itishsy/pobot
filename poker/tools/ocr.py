import ddddocr
import io

from poker.tools.util import match_color, ordered_hand
from poker.models.game import State, Player


class PokerOcr:

    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        self.image = None

        # 7张牌。
        self.hand1_pos = (650, 690)
        self.hand1_suit_pos = (676, 751)
        self.hand2_pos = (718, 690)
        self.hand2_suit_pos = (737, 746)
        self.board_pos = (486, 408)
        self.board_suit_pos = (546, 486)
        self.board_distance = 100
        self.card_wh = (45, 55)
        self.suit_color = ((0, 0, 0), (202, 23, 27), (29, 126, 45), (1, 30, 196))   # 4种花色的rgb

        # 5个玩家: 名称、金额、打出金额。只需定位134,25可计算出来
        self.player1_pos = (185, 655)
        self.player3_pos = (666, 230)
        self.player4_pos = (1090, 310)
        self.player_wh = (175, 31)
        self.player1_bet_pos = (350, 575)
        self.player3_bet_pos = (660, 315)
        self.player4_bet_pos = (945, 355)
        self.player_bet_wh = (175, 35)

        # 底池、位置
        self.region_pool = (729, 368, 817, 398)
        self.color_bottom = (239, 195, 44)  # D标记颜色
        self.position_bottom_0 = (648, 657)  # 我
        self.position_bottom_1 = (392, 634)  # 左下
        self.position_bottom_2 = (392, 353)  # 左上
        self.position_bottom_3 = (672, 303)  # 上
        self.position_bottom_4 = (1057, 353)  # 右上
        self.position_bottom_5 = (1057, 634)  # 右下

        # 余额、跟注金额
        self.region_call_amount = (1047, 856, 1138, 886)
        self.region_balance = (658, 832, 812, 872)

    def fetch_state(self, image):
        self.image = image
        stage = State()
        stage.hand = self.__hand()
        stage.board = self.__board()
        stage.stage = 0 if len(stage.board) == 0 else len(stage.board) - 2
        stage.position = self.__pos()
        stage.pot = self.__ocr_amt(self.region_pool)
        stage.stack = self.__ocr_amt(self.region_balance)
        stage.call = self.__ocr_amt(self.region_call_amount)
        stage.players = self.__players()
        return stage

    def __ocr_txt(self, region):
        crop_image = self.image.crop(region)
        crop_image.save('c:\\Huangsy\\sourcecode\\pobot\\poker\\cropped_image.png')
        image_bytes = io.BytesIO()
        crop_image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        result = self.ocr.classification(image_bytes)
        return result

    def __ocr_amt(self, region):
        ocr_txt = self.__ocr_txt(region)
        if ocr_txt and '全押' not in ocr_txt:
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

    def __get_suit(self, pos):
        color = self.image.getpixel(pos)
        if match_color(self.suit_color[0], color, 20):
            return 's'
        if match_color(self.suit_color[1], color, 20):
            return 'h'
        if match_color(self.suit_color[2], color, 20):
            return 'c'
        if match_color(self.suit_color[3], color, 20):
            return 'd'

    def __players(self):
        pls = []
        w, h, bw, bh = self.player_wh[0], self.player_wh[1], self.player_bet_wh[0], self.player_bet_wh[1]
        self_pos = self.__pos()
        for i in range(1, 6):
            if i in [1, 3, 4]:
                x, y = eval('self.player{}_pos[0]'.format(i)), eval('self.player{}_pos[1]'.format(i))
                bx, by = eval('self.player{}_bet_pos[0]'.format(i)), eval('self.player{}_bet_pos[1]'.format(i))
            elif i == 2:
                x, y = self.player1_pos[0], self.player4_pos[1]
                bx, by = self.player1_bet_pos[0], self.player4_bet_pos[1]
            else:
                x, y = self.player4_pos[0], self.player1_pos[1]
                bx, by = self.player4_bet_pos[0], self.player1_bet_pos[1]
            amount = self.__ocr_amt((bx, by, bx+bw, by+bh))
            position = (self_pos + i) % 6
            pls.append(Player(name=self.__ocr_txt((x, y, x+w, y+h)),
                              position=position if position > 0 else 6,
                              stack=self.__ocr_amt((x, y+h-5, x+w, y+h+h-5)),
                              action='pending',
                              amount=amount))
        return pls

    def __hand(self):
        x1, y1 = self.hand1_pos[0], self.hand1_pos[1]
        x2, y2 = self.hand2_pos[0], self.hand2_pos[1]
        w, h = self.card_wh[0], self.card_wh[1]

        return ordered_hand([self.__ocr_card((x1, y1, x1+w, y1+h), self.hand1_suit_pos),
                             self.__ocr_card((x2, y2, x2+w, y2+h), self.hand2_suit_pos)])

    def __board(self):
        board = []
        x, y = self.board_pos[0], self.board_pos[1]
        w, h = self.card_wh[0], self.card_wh[1]

        for i in range(1, 6):
            x1 = x + (i - 1) * self.board_distance
            suit_pos = (self.board_suit_pos[0]+(i - 1) * self.board_distance, self.board_suit_pos[1])
            card = self.__ocr_card((x1, y, x+w, x1+h), suit_pos)
            if card:
                board.append(card)
            else:
                break
        return board

    def __pos(self):
        pos = -1
        for i in range(6):
            position = eval('self.position_bottom_{}'.format(i))
            color = self.image.getpixel(position)
            if match_color(self.color_bottom, color, 50):
                pos = 6 - i
                break
        return pos
