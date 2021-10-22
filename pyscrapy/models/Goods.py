from sqlalchemy import Column, String, Integer, Float, Text
from . import BaseModel


class Goods(BaseModel):

    __tablename__ = 'goods'
    code = Column(String(64), comment='商品编码')
    category_id = Column(Integer, default=0)
    category_name = Column(String(128), comment='分类名')
    site_id = Column(Integer, default=0)
    # sqlalchemy.exc.DataError: (pymysql.err.DataError) (1406, "Data too long for column 'title' at row 1")
    title = Column(String(255), comment='商品标题')
    image = Column(String(500), comment='图片地址')
    url = Column(String(500), comment='链接地址')
    local_image = Column(String(255), comment='本地图片地址')
    price = Column(Float(8, 2), comment='价格')
    quantity = Column(Integer, default=0)
    status = Column(Integer, default=0, comment='状态。 0:Unknown; 1:Available; 2:SOLD OUT; 3:Unavailable')
    reviews_num = Column(Integer, default=0, comment='评论数')
    # reviews_url = Column(String(500), comment='评论列表地址')
    # sales = Column(Integer, default=0, comment='销量')
    details = Column(Text, comment='详情')

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

