import time

from poker.strategies.strategy import Strategy

from poker.tools.ocr import PokerOcr
from poker.tools.rpa import PokerRpa
from poker.models.game import Game
from poker.ai.ai import PokerAI


class GameAgent:

    def __init__(self):
        self.ocr = PokerOcr()
        self.rpa = PokerRpa()
        self.game = Game()
        self.strategy = Strategy()     # PokerAIAgent()

    def start(self):
        while True:
            image = self.rpa.shot()
            if image:
                state = self.ocr.fetch_state(image)
                self.game.add_state(state)
                print(state.to_dict())
                action = self.strategy.predict_action(self.game)
                self.rpa.do(action)
                time.sleep(3)
            time.sleep(1)


if __name__ == '__main__':
    ga = GameAgent()
    ga.start()

