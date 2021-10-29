from sqlalchemy import Column, DateTime, Integer
from . import BaseModel


class GoodsSkuQuantityLog(BaseModel):

    __tablename__ = 'goods_sku_quantity_log'

    log_id = Column(Integer, comment='爬虫运行记录spider_run_log表的ID')
    goods_id = Column(Integer, default=0)
    sku_id = Column(Integer, default=0)
    quantity = Column(Integer, default=0, comment='库存')
    datetime = Column(DateTime, comment='生成日期')
