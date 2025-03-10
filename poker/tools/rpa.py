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
        self.position_button_call = (1096, 860)
        self.position_button_raise = (1252, 860)
        self.position_button_add_amount = (1301, 787)

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

    def do(self, action, raised=0):
        if action in self.actions:
            print(action, amount)
            if raised > 0:
                pyautogui.moveTo(self.position_button_add_amount[0], self.position_button_add_amount[1], duration=0.2)
                pyautogui.click(clicks=raised, interval=0.3)
            act = getattr(self, '__{}'.format(action))
            act()
            pyautogui.moveTo(POSITION_BUTTON_FOLD[0] + random.randint(1, 100),
                             POSITION_BUTTON_FOLD[1] + random.randint(100, 500) - 800,
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
        pyautogui.moveTo(self.position_button_raise[0] + random.randint(1, 10),
                         self.position_button_raise[1] + random.randint(1, 5),
                         duration=0.2)  # duration 参数表示鼠标移动的时间，这里设置为 1 秒
        pyautogui.click()