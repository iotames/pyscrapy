from email.policy import default
from sqlalchemy import Column, String, Integer, Text, DateTime, BigInteger
from . import BaseModel
from datetime import datetime


class ProductQuantity(BaseModel):

    __tablename__ = BaseModel.table_prefix + 'product_quantities' + BaseModel.table_suffix
    
    product_id = Column(BigInteger, default=0, comment='商品ID')
    time_before = Column(DateTime, comment="最近采集时间")
    quantity_before = Column(Integer, default=0, comment="采集前库存数量")
    quantity_after = Column(Integer, default=0, comment="采集后库存数量")
    quantity_diff = Column(Integer, default=0, comment="销量(库存变化)")
    unix_time = Column(Integer, default=0, comment="UNIX时间戳")

