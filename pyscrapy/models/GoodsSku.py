from sqlalchemy import Column, String, Integer, Float, Text
from . import BaseModel


class GoodsSku(BaseModel):

    __tablename__ = 'goods_sku'

    site_id = Column(Integer, default=0)
    goods_id = Column(Integer, default=0)
    code = Column(String(64), comment='SKU编码')
    category_id = Column(Integer, default=0)
    category_name = Column(String(128), comment='分类名')

    option1 = Column(String(64), comment='规格名1')
    option2 = Column(String(64), comment='规格名2')
    option3 = Column(String(64), comment='规格名3')

    title = Column(String(128), comment='SKU标题')
    full_title = Column(String(255), comment='商品+SKU标题')
    image = Column(String(500), comment='图片地址')

    inventory_quantity = Column(Integer, default=0, comment='库存数')
    barcode = Column(String(64), comment='条形码')
    price = Column(Float(8, 2), comment='价格')

    local_image = Column(String(255), comment='本地图片地址')
    # reviews_num = Column(Integer, default=0, comment='评论数')
    # reviews_url = Column(String(500), comment='评论列表地址')
    # sales = Column(Integer, default=0, comment='销量')

