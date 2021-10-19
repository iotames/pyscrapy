from sqlalchemy import Column, String, DateTime
from . import BaseModel, Goods


class SpiderRunLog(BaseModel):
    # 爬虫运行记录表

    __tablename__ = 'spider_run_log'

    spider_name = Column(String(64), comment='爬虫名')
    spider_child = Column(String(64), default='子爬虫名')
    datetime = Column(DateTime, comment='运行日期')
