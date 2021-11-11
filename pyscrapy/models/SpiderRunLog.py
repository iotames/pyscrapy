from sqlalchemy import Column, String, DateTime, SmallInteger
from . import BaseModel, Goods


class SpiderRunLog(BaseModel):
    # 爬虫运行记录表

    __tablename__ = 'spider_run_log'

    STATUS_READY = 0
    STATUS_RUNNING = 1
    STATUS_PAUSE = 2
    STATUS_DONE = 3

    spider_name = Column(String(64), comment='爬虫名')
    spider_child = Column(String(64), default='子爬虫名')
    datetime = Column(DateTime, comment='运行日期')
    status = Column(SmallInteger, comment='运行状态')
