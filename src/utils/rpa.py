import pyautogui
import random

from config.gg import process_config
from tools.ocr import match_color


class PokerRpa:

    def __init__(self):
        self.win_title = "192.168.0.113 - 远程桌面连接"
        self.win = None
        self.image = None

        self.actions = ['fold', 'call', 'check', 'bet', 'raise', 'allin']
        ocr_config = process_config()

        # 按鈕识别
        self.color_button = ocr_config['action']['color']   # (171, 67, 63)
        self.position_button_fold = ocr_config['action']['fold']   # (937, 860)
        self.position_button_call = ocr_config['action']['call']   # (1096, 860)
        self.position_button_raise = ocr_config['action']['raise']   # (1252, 860)
        self.position_button_add_amount = ocr_config['action']['add']   # (1301, 787)

    def __get_win(self):
        if self.win is None:
            wins = pyautogui.getWindowsWithTitle(self.win_title)
            if wins and wins[0] and (wins[0].left >= -50 or wins[0].top >= -50):
                self.win = wins[0]
        return self.win

    def shot_win(self):
        win = self.__get_win()
        if win:
            image = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
            # image.save('image.png')
            button_color = image.getpixel(self.position_button_fold)
            # print(button_color, self.color_button)
            if match_color(button_color, self.color_button, diff=100):
                # print('return image')
                self.image = image
                return image
        # print('none image')
        return None

    def do_action(self, action, raised=0):
        if self.win and action in self.actions:
            print(action, raised)
            if raised > 0:
                pyautogui.moveTo(self.position_button_add_amount[0], self.position_button_add_amount[1], duration=0.2)
                pyautogui.click(clicks=raised, interval=0.3)
            if 'fold' == action:
                self.__fold()
            elif 'call' == action or 'check' == action:
                self.__call()
            elif 'raise' == action or 'bet' == action:
                self.__raise()
            pyautogui.moveTo(self.position_button_fold[0] + random.randint(-100, 100),
                             self.position_button_fold[1] + random.randint(100, 300) - 800,
                             duration=0.8)  # duration 参数表示鼠标移动的时间
        else:
            print('undefined action:', action)

    def __fold(self):
        pyautogui.moveTo(self.position_button_fold[0] + random.randint(1, 10),
                         self.position_button_fold[1] + random.randint(1, 5),
                         duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        pyautogui.click()

    def __check(self):
        pyautogui.moveTo(self.position_button_call[0] + random.randint(1, 10),
                         self.position_button_call[1] + random.randint(1, 5),
                         duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        pyautogui.click()

    def __call(self):
        pyautogui.moveTo(self.position_button_call[0] + random.randint(1, 10),
                         self.position_button_call[1] + random.randint(1, 5),
                         duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        pyautogui.click()

    def __raise(self):
        button_color = self.image.getpixel(self.position_button_raise)
        if match_color(button_color, self.color_button, diff=100):
            pyautogui.moveTo(self.position_button_raise[0] + random.randint(1, 10),
                             self.position_button_raise[1] + random.randint(1, 5),
                             duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        else:
            pyautogui.moveTo(self.position_button_call[0] + random.randint(1, 10),
                             self.position_button_call[1] + random.randint(1, 5),
                             duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        pyautogui.click()
