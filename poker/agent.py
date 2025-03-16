import time

from poker.strategies.default_strategy import Strategy

from poker.tools.ocr import PokerOcr
from poker.tools.rpa import PokerRpa
from poker.models.game import Game
from poker.ai.ai import PokerAI


class GameAgent:

    def __init__(self):
        self.ocr = PokerOcr()
        self.rpa = PokerRpa()
        self.game = Game()
        self.strategy = Strategy()
        self.ai = PokerAI(drl=False)    # 开启深度机器学习

    def start(self):
        while True:
            image = self.rpa.shot()
            if image:
                try:
                    state = self.ocr.fetch_state(image)
                    self.game.add_state(state)
                    print(state.to_dict())
                    action, raised = self.ai.eval_action(self.game)
                    self.rpa.do(action, raised=raised)
                except:
                    self.rpa.do('fold', raised=0)
                time.sleep(3)
            time.sleep(2)


if __name__ == '__main__':
    ga = GameAgent()
    ga.start()

