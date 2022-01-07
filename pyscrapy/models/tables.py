from pyscrapy.models import *
from sqlalchemy.engine import Engine
from Config import Config
from service import DB


class Table:

    @classmethod
    def create_all_tables(cls, engine: Engine):
        BaseModel.metadata.create_all(engine)

