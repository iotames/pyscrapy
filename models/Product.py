from email.policy import default
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from . import BaseModel
from datetime import datetime


class Product(BaseModel):

    __tablename__ = 'products'
    collected_at = Column(DateTime, default=datetime.now())
    code = Column(String(64), comment='商品编码')
    spu = Column(String(64), comment='SPU')
    merchant_id = Column(Integer, default=0, comment='商户ID店铺ID')
    category_id = Column(Integer, default=0)
    sort = Column(Integer, default=0)
    category_name = Column(String(128), comment='分类名')
    site_id = Column(Integer, default=0)

    title = Column(String(255), comment='商品标题')
    image = Column(String(500), comment='图片地址')
    url = Column(String(500), comment='链接地址')
    local_image = Column(String(255), comment='本地图片地址')
    price = Column(Float(8, 2), comment='价格', default=0.0)
    original_price = Column(Float(8, 2), comment='原价', default=0.0)
    price_text = Column(String(32), comment='价格包含单位')

    quantity = Column(Integer, default=0, comment="库存数量")
    status = Column(Integer, default=0, comment='状态。 0:Unknown; 1:Available; 2:SOLD OUT; 3:Unavailable')

    reviews_num = Column(Integer, default=0, comment='评论数')
    variants_num = Column(Integer, default=0, comment='变体数')
    sales_num = Column(Integer, default=0, comment='销量')
    sales_num_last_month = Column(Integer, default=0, comment='上月销量')


    detail = Column(Text, comment='详情')

    STATUS_UNKNOWN = 0
    STATUS_AVAILABLE = 1
    STATUS_SOLD_OUT = 2
    STATUS_UNAVAILABLE = 3
    statuses_map = {
        STATUS_UNKNOWN: 'Unknown',
        STATUS_AVAILABLE: 'Available',
        STATUS_SOLD_OUT: 'SOLD OUT',
        STATUS_UNAVAILABLE: 'Unavailable'
    }




