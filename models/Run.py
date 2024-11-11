from sqlalchemy.engine import Engine
from . import BaseModel
# from . import *

class Run:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        BaseModel.metadata.create_all(engine)