from sqlalchemy import Column, DateTime, Integer
from . import BaseModel


class GoodsQuantityLog(BaseModel):

    __tablename__ = 'goods_quantity_log'

    log_id = Column(Integer, comment='爬虫运行记录spider_run_log表的ID')
    goods_id = Column(Integer, default=0)
    quantity = Column(Integer, default=0, comment='库存')
    datetime = Column(DateTime, comment='生成日期')
