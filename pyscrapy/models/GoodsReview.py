from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from . import BaseModel


class GoodsReview(BaseModel):

    __tablename__ = 'goods_review'

    site_id = Column(Integer, default=0)
    goods_id = Column(Integer, default=0)
    code = Column(String(64), comment='评论ID')
    goods_code = Column(String(64), comment='商品编码')
    goods_spu = Column(String(64), comment='商品SPU')
    rating_value = Column(Integer, default=0, comment='评分星级1-5')
    title = Column(String(255), comment='评论标题')
    sku_text = Column(String(128), comment='颜色规格')
    url = Column(String(255), comment='链接地址')
    color = Column(String(64), comment='颜色')
    review_date = Column(DateTime, comment='评论时间')
    review_time = Column(Integer, comment='评论时间戳')
    time_str = Column(String(64), comment='评论时间')
    body = Column(Text, comment='评论内容')

    age = Column(String(32), comment='年龄')
    body_type = Column(String(255), comment='体型')
    activity = Column(String(255), comment="activity")

