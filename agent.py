import time
from datetime import datetime


from ocr import PokerOcr
from rpa import PokerRpa
from models.game import Game
from ai.ai import PokerAI


class GameAgent:

    def __init__(self):
        self.ocr = PokerOcr()
        self.rpa = PokerRpa()
        self.game = Game()
        self.ai = PokerAI(drl=False)    # 开启深度机器学习

    def start(self):
        while True:
            try:
                image = self.rpa.shot_win()
                if image:
                    state = self.ocr.fetch_state(image)
                    self.game.add_state(state)
                    print(state.to_dict())
                    action, raised = self.ai.eval_action(self.game)
                    if state.stack > 0:
                        self.rpa.do_action(action, raised=raised)
                    time.sleep(6 if action == 'fold' else 3)
                    # print('sleep 3')
            except Exception as e:
                print('[Error]', str(e))
                self.rpa.shot().save('image/{}.jpg'.format(datetime.now().strftime('%m%d%H%M%S')))
                self.rpa.do_action('fold', raised=0)
            # time.sleep(2)
            # print('sleep 2')


if __name__ == '__main__':
    ga = GameAgent()
    ga.start()

