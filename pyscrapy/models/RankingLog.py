from sqlalchemy import Column, String, Integer, DateTime
from . import BaseModel


class RankingLog(BaseModel):

    __tablename__ = 'ranking_log'

    TYPE_TOP_REVIEWS = 0

    site_id = Column(Integer, default=0)
    rank_type = Column(Integer, comment='排序方式', default=0)
    rank_name = Column(String(64), comment='排序方式')
    category_id = Column(Integer, comment='排名分类ID', default=0)
    category_name = Column(String(64), comment='排名分类名')
    category_code = Column(String(64), comment='排名分类code')
    rank_date = Column(DateTime, comment='排名日期')

