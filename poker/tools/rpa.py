import pyautogui
from PIL import Image

from poker.tools.util import match_color


class PokerRpa:

    def __init__(self):
        self.win_title = "192.168.0.113 - 远程桌面连接"
        self.win = None

        self.actions = ['fold', 'call', 'check', 'bet', 'raise', 'allin']

        # 按鈕识别
        self.color_button = (171, 67, 63)
        self.position_button_fold = (937, 860)

    def __get_win(self):
        if self.win is None:
            wins = pyautogui.getWindowsWithTitle(self.win_title)
            if wins and wins[0] and (wins[0].left >= -10 or wins[0].top >= -10):
                self.win = wins[0]
        return self.win

    def shot(self):
        win = self.__get_win()
        if win:
            image = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
            if match_color(image.getpixel(self.position_button_fold), self.color_button, diff=10):
                return image
        return None

    def do(self, action, amount=0.0):
        if action in self.actions:
            print(action, amount)
        else:
            print('undefined action:', action)


