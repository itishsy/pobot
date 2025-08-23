import json


class Player:

    def __init__(self, name, position, stack, action, active, amount=None):
        self.name = name
        self.active = active
        self.position = position
        self.stack = stack
        self.action = action
        self.amount = round(amount, 2) if amount is not None else 0.0

    def to_dict(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def to_str(self, simple=False):
        if simple:
            return '{},{},{}'.format(self.position, self.name, self.stack)
        return '{},{},{},{}'.format(self.name, self.stack, self.action, self.amount)

    @staticmethod
    def new_from_dict_str(dict_str):
        if dict_str != '':
            dic = json.loads(dict_str)
            return Player(name=dic['name'],
                          position=dic['position'],
                          stack=dic['stack'],
                          active=dic['active'],
                          action=dic['action'],
                          amount=dic['amount'])

