from models.base import BaseModel, db
from flask_peewee.db import CharField, IntegerField, DateTimeField, AutoField, DecimalField


class Player(BaseModel):
    id = AutoField()
    game_code = CharField()
    name = CharField()
    seat = CharField()
    status = CharField()
    amount = DecimalField()  # 起始金额
    actions = []

    # def eval_player_actions(self, sections, idx):
    #     s_len = len(sections)
    #     if s_len > len(self.actions):
    #         return
    #
    #     if 'fold' == self.actions[-1].action:
    #         return
    #
    #     pre_section = sections[-2]
    #     cur_section = sections[-1]
    #
    #     for i in range(1, s_len):
    #         if self.actions[i].action == 'pending':
    #             if sections[i - 1].pool < sections[i].pool and self.actions[i - 1].amount > self.actions[i].amount:
    #                 self.actions[i].action = 'bet:{}'.format(self.actions[i - 1].amount - self.actions[i].amount)
    #
    #     for i in range(1, s_len):
    #         is_pool_raised = sections[i - 1].pool < sections[i].pool
    #         pre_action = self.actions[i - 1].action
    #
    #         if 'pending' in pre_action:
    #             if is_pool_raised:
    #                 if self.actions[i - 1].amount <= self.actions[i].amount:
    #                     self.actions[i - 1].action = 'fold'
    #             else:
    #                 self.actions[i - 1].action = 'check'
    #         else:
    #             self.actions[i].action = 'check'


# def eval_players_action(players, sections):
#     if len(sections) == 1:
#     else:
#         pre_section = sections[-2]
#         cur_section = sections[-1]
#         i = 0
#         for player in players:
#             pre_amount = p
#             if player.eval_bet_amount()


class PlayerAction:
    player_id = IntegerField()
    stage = CharField()
    round = IntegerField()
    action = CharField()
    amount = DecimalField()

