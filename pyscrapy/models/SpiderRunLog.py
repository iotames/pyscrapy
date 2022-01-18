from sqlalchemy import Column, String, DateTime, SmallInteger, Integer
from . import BaseModel, Goods


class SpiderRunLog(BaseModel):
    # 爬虫运行记录表

    __tablename__ = 'spider_run_log'

    STATUS_READY = 0
    STATUS_RUNNING = 1
    STATUS_PAUSE = 2
    STATUS_DONE = 3
    STATUS_FAIL = 4
    STATUS_MAP = {
        None: "未知",
        STATUS_READY: "待命中",
        STATUS_RUNNING: "运行中",
        STATUS_PAUSE: "已暂停",
        STATUS_DONE: "已完成",
        STATUS_FAIL: "失败"
    }

    spider_name = Column(String(64), comment='爬虫名')
    spider_child = Column(String(64), default='子爬虫名')
    datetime = Column(DateTime, comment='运行日期')
    link_id = Column(String(255), comment='连接ID')
    status = Column(SmallInteger, comment='运行状态')
