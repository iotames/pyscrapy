from sqlalchemy import Column, String, Integer
from . import BaseModel


class GoodsCategoryX(BaseModel):

    __tablename__ = 'goods_category_x'

    goods_id = Column(Integer, default=0)
    category_id = Column(Integer, default=0)
