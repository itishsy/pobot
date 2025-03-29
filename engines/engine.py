from abc import ABC, abstractmethod
from models.choice import Choice
from models.symbol import Symbol
from models.signal import Signal
from common.utils import *


engines = {}


def job_engine(cls):
    cls_name = cls.__name__.lower()[0] + cls.__name__[1:]

    def register(clz):
        engines[cls_name] = clz

    return register(cls)


class Searcher(ABC):
    strategy = 'searcher'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        count = 0
        Choice.delete().where(Choice.strategy == self.strategy).execute()
        symbols = Symbol.actives()
        for sym in symbols:
            try:
                count = count + 1
                co = sym.code
                print('[{0}] {1} searching by {2} ({3}) '.format(datetime.now(), co, self.strategy, count))
                sig = self.search(co)
                if sig:
                    sig.code = co
                    sig.strategy = self.strategy
                    sig.stage = 'choice'
                    sig.upset()

                    # if not Choice.select().where((Choice.code == co) & (Choice.strategy == self.strategy)).exists():
                    #     cho = Choice.create(code=co, name=sym.name, strategy=self.strategy, dt=sig.dt, price=sig.price, freq=sig.freq, status=1, created=datetime.now(), updated=datetime.now())
                    #     Signal.update(oid=cho.id).where((Signal.code == co) & (Signal.strategy == self.strategy)).execute()
            except Exception as e:
                print(e)
        print('[{0}] search {1} done! ({2}) '.format(datetime.now(), self.strategy, count))

    @abstractmethod
    def search(self, code):
        pass


class Watcher(ABC):
    strategy = 'watcher'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        symbols = Symbol.select().where(Symbol.status == 1, Symbol.is_watch == 1)
        for sym in symbols:
            try:
                sig = self.watch(sym.code)
                if sig and not Signal.select().where(Signal.dt == sig.dt and Signal.code == sym.code):
                    sig.code = sym.code
                    sig.name = sym.name
                    sig.stage = 'watch'
                    sig.notify = 0
                    sig.upset()
            except Exception as e:
                print(e)

    @abstractmethod
    def watch(self, code):
        pass


class Fetcher(ABC):
    strategy = 'fetcher'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        self.fetch()

    @abstractmethod
    def fetch(self):
        pass


class Sender(ABC):
    strategy = 'sender'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        self.send()

    @abstractmethod
    def send(self):
        pass
