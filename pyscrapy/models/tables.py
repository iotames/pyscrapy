from pyscrapy.models import BaseModel, Site, Goods, GoodsSku, GoodsCategory, SiteMerchant, \
    GoodsCategoryX, SpiderRunLog, GoodsQuantityLog, GoodsSkuQuantityLog
from sqlalchemy.engine import Engine
from Config import Config
from service import DB


class Table:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        BaseModel.metadata.create_all(engine)


if __name__ == '__main__':
    config = Config()
    db = DB(config.get_database())
    db.ROOT_PATH = config.ROOT_PATH
    db_engine = db.get_db_engine()
    Table.create_all_tables(db_engine)
