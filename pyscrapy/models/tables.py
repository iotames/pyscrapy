from . import BaseModel, Site, Goods, GoodsSku, GoodsCategory, SiteMerchant
from sqlalchemy.engine import Engine


class Table:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        BaseModel.metadata.create_all(engine)
