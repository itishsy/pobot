from config.db import BaseModel, db
from peewee import CharField, AutoField, FloatField

class HandScore(BaseModel):
    class Meta:
        table_name = 'hand_score'

    id = AutoField()
    hand = CharField()
    score = FloatField()

    @staticmethod
    def get_score(card1, card2):
        hs = HandScore.select().where((HandScore.hand == (card1 + card2)) | (HandScore.hand == (card2 + card1))).first()
        return hs.score

    @staticmethod
    def get_ranges(min_score, max_score):
        ranges = []
        lis = HandScore.select().where((HandScore.score >= min_score) & (HandScore.score <= max_score))
        for hs in lis:
            ranges.append(hs.hand)
        return ranges
