from sqlalchemy import Column, String, Integer
from . import BaseModel
# from sqlalchemy.engine import Engine


class GoodsCategory(BaseModel):

    __tablename__ = 'goods_category'

    site_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    name = Column(String(64))
    url = Column(String(255))

    # AttributeError: module 'pyscrapy.models.GoodsCategory' has no attribute 'create_table'
    # @classmethod
    # def create_table(cls, engine: Engine):
    #     cls.__table__.create(engine, checkfirst=True)

