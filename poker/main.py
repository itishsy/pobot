import time
import io
import ddddocr
import os

from poker.game import Game, Section
from poker.action import Action
from poker.utils import *
from poker.strategies.strategy import Strategy
from ai.agent import PokerAIAgent


class TableImage:

    def __init__(self, image, ocr):
        self.image = image
        self.ocr = ocr

    def is_open(self):
        color = self.image.getpixel(POSITION_READY)
        return is_match_color(color, COLOR_READY, 50)

    def ocr_txt(self, region):
        x1 = WIN_OFFSET[0] + region[0]
        y1 = WIN_OFFSET[1] + region[1]
        x2 = WIN_OFFSET[0] + region[0] + region[2]
        y2 = WIN_OFFSET[1] + region[1] + region[3]
        # self.image.save("aaa.jpg")
        region_image = self.image.crop((x1, y1, x2, y2))
        # region_image.save(cropped_image)
        image_bytes = io.BytesIO()
        region_image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        result = self.ocr.classification(image_bytes)
        return result

    def fetch_card(self, idx):
        region = get_region('CARD', idx)
        ocr_txt = self.ocr_txt(region)
        card_text = fetch_card(ocr_txt, idx)
        if card_text is not None:
            if idx > 3:
                suit_position = (POSITION_SUIT_3[0] + PUB_CARD_SPACE_X*(idx-3), POSITION_SUIT_3[1])
            else:
                suit_position = eval('POSITION_SUIT_' + str(idx))
            color = self.image.getpixel(suit_position)
            if is_match_color(SUIT_COLOR[0], color, 20):
                return card_text + 's'
            if is_match_color(SUIT_COLOR[1], color, 20):
                return card_text + 'h'
            if is_match_color(SUIT_COLOR[2], color, 20):
                return card_text + 'c'
            if is_match_color(SUIT_COLOR[3], color, 20):
                return card_text + 'd'

    def fetch_player(self, idx):
        (region_name, region_amount) = get_region('PLAYER', idx)
        name = self.ocr_txt(region_name)
        amount_txt = self.ocr_txt(region_amount)
        amount = fetch_amount(amount_txt)
        return name, amount

    def fetch_pool(self):
        region = get_region('POOL')
        ocr_txt = self.ocr_txt(region)
        return fetch_amount(ocr_txt)

    def fetch_seat(self):
        for i in range(6):
            position = eval('POSITION_BOTTOM_' + str(i))
            color = self.image.getpixel(position)
            if is_match_color(COLOR_BOTTOM, color, 50):
                return 6 - i
        return -1

    def create_section(self):
        pool = self.fetch_pool()
        card1 = self.fetch_card(1)
        seat = self.fetch_seat()
        if not pool or not card1 or not seat:
            return

        sec = Section()
        sec.pool = pool
        sec.seat = seat
        sec.stage = 'PreFlop'
        sec.card1 = card1
        sec.card2 = self.fetch_card(2)
        sec.card3 = self.fetch_card(3)
        if sec.card3:
            sec.stage = 'Flop'
            sec.card4 = self.fetch_card(4)
            sec.card5 = self.fetch_card(5)
            sec.card6 = self.fetch_card(6)
            if sec.card6:
                sec.card7 = self.fetch_card(7)
                sec.stage = 'River' if sec.card7 else 'Turn'

        sec.player1_name, sec.player1_amount = self.fetch_player(1)
        sec.player2_name, sec.player2_amount = self.fetch_player(2)
        sec.player3_name, sec.player3_amount = self.fetch_player(3)
        sec.player4_name, sec.player4_amount = self.fetch_player(4)
        sec.player5_name, sec.player5_amount = self.fetch_player(5)

        amount_txt = self.ocr_txt(REGION_CALL_AMOUNT)
        sec.call_txt = amount_txt
        if amount_txt.strip().startswith('S') or amount_txt.strip().startswith('s'):
            call_amount = fetch_amount(amount_txt)
        else:
            call_amount = 0.0
        sec.call = call_amount

        return sec


class GameEngine:

    def __init__(self):
        self.ocr = ddddocr.DdddOcr()
        self.game = None
        self.win = None
        self.is_start = False
        self.game_info = ''

    def active(self):
        try:
            if not self.is_start:
                win = get_win()
                if win and (win.left >= 0 or win.top >= 0):
                    self.win = win
                    img = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
                    self.is_start = is_match_color(img.getpixel(POSITION_READY), COLOR_READY)
                    if self.is_start:
                        print("start")
                        return True
                    else:
                        print("ready")
                else:
                    print("no window")
            self.is_start = self.win.left > -100 or self.win.top > -100
        except:
            self.is_start = False
        return self.is_start

    def load_game(self, section):
        if self.is_new_game(section):
            reward = section.balance - self.game.sections[-1].balance
            self.game = Game(section)
            return True
        if not section.equals(self.game.sections[-1]):
            self.game.append_section(section)
            return True
        return False

    def is_new_game(self, section):
        return (not self.game
                or self.game.card1 != section.card1
                or self.game.card2 != section.card2
                or self.game.seat != section.seat)

    def do_action(self):
        self.print()
        action = Action(self.game.action)
        action.do()
        self.game.action = None

    def print(self):
        if not self.game_info or self.game_info != self.game.get_info():
            self.game_info = self.game.get_info()
            print('-----', self.game_info, '-----')

        sec = self.game.sections[-1]
        if sec.card3:
            print("pool: {}, 公共牌: {}-{}-{}-{}-{}, call: {}".format(
                sec.pool, self.game.card3, self.game.card4, self.game.card5,
                self.game.card6, self.game.card7, sec.call))
        else:
            print("pool: {}, call: {}".format(sec.pool, sec.call))

        if len(self.game.sections) > 1:
            for player in self.game.players:
                if player.actions and player.actions[-1].action != 'fold':
                    print("{}: {}, {}".format(player.name, player.seat, player.actions[-1].action))

        if self.game.action:
            print("{} : hand_score --> {} action --> {}".format(
                self.game.stage, self.game.sections[-1].hand_score, self.game.action))

    def start(self):
        agent = PokerAIAgent()
        strategy = Strategy()
        while True:
            if self.active():
                image = pyautogui.screenshot(region=(self.win.left, self.win.top, self.win.width, self.win.height))
                if is_match_color(image.getpixel(POSITION_BUTTON_FOLD), COLOR_BUTTON):
                    table = TableImage(image, self.ocr)
                    sec = table.create_section()
                    if sec and sec.enabled() and self.load_game(sec):
                        # self.game.action = strategy.predict_action(self.game)
                        self.game.action = agent.predict_action(sec.get_state())
                        agent.learn(sec.balance)
                        sec.action = self.game.action
                        if sec.stage == 'PreFlop' and sec.action == 'fold' and len(self.game.sections) == 1:
                            # PreFlop第一輪就fold掉的，不保存
                            pass
                        else:
                            sec.save()
                            os.makedirs('image/{}'.format(self.game.code), exist_ok=True)
                            image.save('image/{}/{}.jpg'.format(self.game.code, sec.id))
                    self.do_action()
            time.sleep(2)


def test_workflow(file_name='table_image.jpg'):
    wf1 = GameEngine()
    tab1 = TableImage(Image.open(file_name), wf1.ocr)
    sec1 = tab1.create_section()
    if wf1.load_game(sec1):
        wf1.print()


if __name__ == '__main__':
    # ge = GameEngine()
    # ge.start()
    test_workflow('image/20250209132704/2.jpg')

