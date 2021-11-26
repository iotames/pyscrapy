from sqlalchemy import Column, String, Integer, Float, Text
from . import BaseModel


class GoodsReview(BaseModel):

    __tablename__ = 'goods_review'

    site_id = Column(Integer, default=0)
    goods_id = Column(Integer, default=0)
    code = Column(String(64), comment='评论ID')
    rating_value = Column(Integer, default=0, comment='评分星级1-5')
    title = Column(String(255), comment='评论标题')
    sku_text = Column(String(128), comment='颜色规格')
    url = Column(String(255), comment='链接地址')
    color = Column(String(64), comment='颜色')
    review_date = Column(String(32), comment='评论时间')
    body = Column(Text, comment='评论内容')
