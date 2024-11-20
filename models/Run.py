from sqlalchemy.engine import Engine
from . import BaseModel
# from . import *
from sqlalchemy import text

class Run:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        try:
            BaseModel.metadata.create_all(engine)
        except Exception as e:
            raise e

    @classmethod
    def drop_all_tables(cls, engine: Engine):
        try:
            BaseModel.metadata.drop_all(engine)
        except Exception as e:
            raise e
    
    @classmethod
    def truncate_all_tables(cls, engine: Engine):
        for table in metadata.tables.values():
            with engine.connect() as connection:
                connection.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

  