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
        # 继承此基类的模型类，通过此方法创建3张数据表。 后面报错： no attribute create_mydb_table 原因未知。 2021-10-13
        # 导入包含基类的所有模型类后，执行 基类的 .metadata.create_all(engine) 静态方法，解决此问题。
        cls.__table__.create(engine, checkfirst=True)
        # Base.metadata.create_all(engine)

# BaseModel = declarative_base(cls=AlchemyBase)
