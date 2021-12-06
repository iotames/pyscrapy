from sqlalchemy import Column, String, Integer
from . import BaseModel


class RankingGoods(BaseModel):

    __tablename__ = 'ranking_goods'

    site_id = Column(Integer, default=0)
    ranking_log_id = Column(Integer, default=0)
    spider_run_log_id = Column(Integer, default=0)
    rank_num = Column(Integer, comment='当前排名')
    goods_id = Column(Integer, default=0)
    goods_code = Column(String(64))
    goods_spu = Column(String(64))
    goods_title = Column(String(255))


