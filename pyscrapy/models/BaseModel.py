from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
import time
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session
from Config import Config
from pyscrapy.database import Database

AlchemyBase = declarative_base()

# class AlchemyBase(object):


class BaseModel(AlchemyBase):

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

    @staticmethod
    def get_db_session() -> Session:
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        return db.get_db_session()

    @classmethod
    def get_model(cls, db_session, args: dict):
        model = db_session.query(cls).filter_by(**args).first()
        return model

    @classmethod
    def update_model(cls, db_session: Session, update_data: dict, find_by: dict):
        db_session.query(cls).filter_by(**find_by).update(update_data)

    @classmethod
    def create_model(cls, db_session: Session, args: dict):
        model = cls(**args)
        db_session.add(model)

    @classmethod
    def get_all_model(cls, db_session: Session, args=None) -> list:
        return db_session.query(cls).filter_by(**args).all()

# BaseModel = declarative_base(cls=AlchemyBase)
