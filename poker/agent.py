import time
from datetime import datetime


from poker.tools.ocr import PokerOcr
from poker.tools.rpa import PokerRpa
from poker.models.game import Game
from poker.ai.ai import PokerAI


class GameAgent:

    def __init__(self):
        self.ocr = PokerOcr()
        self.rpa = PokerRpa()
        self.game = Game()
        self.ai = PokerAI(drl=False)    # 开启深度机器学习

    def start(self):
        while True:
            # try:
                image = self.rpa.shot()
                if image:
                    state = self.ocr.fetch_state(image)
                    self.game.add_state(state)
                    print(state.to_dict())
                    action, raised = self.ai.eval_action(self.game)
                    self.rpa.do(action, raised=raised)
                    time.sleep(6 if action == 'fold' else 3)
                    # print('sleep 3')
            # except Exception as e:
            #     print('[Error]', str(e))
                # image.save('image/{}.jpg'.format(datetime.now().strftime('%m%d%H%M%S')))
                # self.rpa.do('fold', raised=0)
            # time.sleep(2)
            # print('sleep 2')


if __name__ == '__main__':
    ga = GameAgent()
    ga.start()

