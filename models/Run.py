from sqlalchemy.engine import Engine
from . import BaseModel
# from . import *

class Run:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        try:
            BaseModel.metadata.create_all(engine)
        except Exception as e:
            raise e