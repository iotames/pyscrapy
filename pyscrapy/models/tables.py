from . import Site, Goods, GoodsSku, GoodsCategory
from sqlalchemy.engine import Engine


class Table:

    @staticmethod
    def get_models_class_list():
        return [
            Site,
            Goods,
            GoodsSku,
            # GoodsCategory
        ]

    @classmethod
    def create_all_tables(cls, engine: Engine):
        for model in cls.get_models_class_list():
            if model == GoodsCategory:
                GoodsCategory.__table__.create(engine, checkfirst=True)
            else:
                model.create_mydb_table(engine)
