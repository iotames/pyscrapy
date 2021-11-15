from sqlalchemy import Column, String, SMALLINT
from . import BaseModel


class Translator(BaseModel):

    __tablename__ = 'translator'

    from_lang = Column(String(255), comment='原文')
    to_lang = Column(String(255), comment='译文')
    trans_type = Column(SMALLINT, default=0, comment='翻译类型。默认英译汉0')
