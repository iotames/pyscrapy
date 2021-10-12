from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
import time
from sqlalchemy.engine import Engine

AlchemyBase = declarative_base()


class BaseModel(AlchemyBase):
# class AlchemyBase(object):

    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(Integer, default=int(time.time()))
    updated_at = Column(Integer, default=int(time.time()))

    @classmethod
    def create_mydb_table(cls, engine: Engine):
        cls.__table__.create(engine, checkfirst=True)
        # Base.metadata.create_all(engine)

# BaseModel = declarative_base(cls=AlchemyBase)
