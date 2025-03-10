import time
from PIL import Image

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
        self.pokerAi = PokerAI()

    def predict_action(self, ai=False):
        if ai:
            game_state = self.game.states[-1]
            return self.pokerAi.eval_action(game_state)
        else:
            return self.strategy.eval_action(self.game)

    def start(self):
        while True:
            image = self.rpa.shot()
            if image:
                state = self.ocr.fetch_state(image)
                self.game.add_state(state)
                print(state.to_dict())
                action, raised = self.predict_action()
                self.rpa.do(action, raised=raised)
                time.sleep(3)
            time.sleep(2)

    def test_ocr(self):
        img1 = Image.open('image/20250209132704/2.jpg')
        state = self.ocr.fetch_state(img1)
        print(state.to_dict())


if __name__ == '__main__':
    ga = GameAgent()
    # ga.start()
    ga.test_ocr()

