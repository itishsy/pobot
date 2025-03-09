
from poker.strategies.strategy import Strategy

from poker.tools.ocr import PokerOcr
from poker.tools.rpa import PokerRpa
from poker.models.game import Game
from ai.agent import PokerAIAgent


class GameEngine:

    def __init__(self):
        self.ocr = PokerOcr()
        self.rpa = PokerRpa()
        self.game = Game()
        self.agent = Strategy()     # PokerAIAgent()

    def start(self):
        while True:
            image = self.rpa.shot()
            if image:
                state = self.ocr.fetch_state(image)
                self.game.add_state(state)
                print(state.to_dict())
                action = self.agent.predict_action(self.game)
                self.rpa.do(action)


if __name__ == '__main__':
    ge = GameEngine()
    ge.start()

