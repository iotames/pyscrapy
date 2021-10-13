from sqlalchemy import Column, String, Integer
from . import BaseModel


class GoodsCategory(BaseModel):

    __tablename__ = 'goods_category'

    site_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    name = Column(String(64))
    url = Column(String(255))
