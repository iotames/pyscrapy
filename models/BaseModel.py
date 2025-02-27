from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, DateTime
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import Session
from service import Config, DB, Snowflake
# from pyscrapy.database import Database

AlchemyBase = declarative_base()

# class AlchemyBase(object):

class BaseModel(AlchemyBase):
    
    # 定义表名前缀和后缀
    table_prefix = 'ods_cwr_end_'
    table_suffix = '_nd'
    __abstract__ = True
    __table_args__ = {'schema': Config.get_database()['db_schema']} # "craw"
    
    id = Column(BigInteger, primary_key=True, default=Snowflake.get_instance(1, 1).get_next_id())
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime, default=None)

    # 重写 __tablename__ 属性
    @classmethod
    def __tablename__(cls):
        return cls.table_prefix + cls.__name__.lower() + cls.table_suffix
    
    @classmethod
    def create_mydb_table(cls, engine: Engine):
        # 继承此基类的模型类，通过此方法创建3张数据表。 后面报错： no attribute create_mydb_table 原因未知。 2021-10-13
        # 导入包含基类的所有模型类后，执行本基类的 .metadata.create_all(engine) 静态方法，解决此问题。
        cls.__table__.create(engine, checkfirst=True)

    @staticmethod
    def get_db_session() -> Session:
        return DB.get_instance(Config.get_database()).get_db_session()

    @classmethod
    def get_one(cls, args: dict):
        return cls.get_db_session().query(cls).filter_by(**args).first()

    @classmethod
    def save_create(cls, attr: dict):
        db_session = cls.get_db_session()
        model = cls(**attr)
        db_session.add(model)
        db_session.commit()
        return model

    @classmethod
    def save_update(cls, find_by: dict, update_data: dict):
        db_session = cls.get_db_session()
        db_session.query(cls).filter_by(**find_by).update(update_data)
        db_session.commit()

    @classmethod
    def get_all(cls, args=None) -> list:
        return cls.get_db_session().query(cls).filter_by(**args).all()
    
    @classmethod
    def query(cls, args=None):
        if args is None:
            return cls.get_db_session().query(cls)
        return cls.get_db_session().query(*args)
    
    @staticmethod
    def getSnowflake():
        return Snowflake.get_instance(1, 1)

# BaseModel = declarative_base(cls=AlchemyBase)
