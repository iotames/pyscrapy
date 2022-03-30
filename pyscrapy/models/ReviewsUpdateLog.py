import time

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from . import BaseModel, Goods
from sqlalchemy import and_
from datetime import datetime


class ReviewsUpdateLog(BaseModel):

    __tablename__ = 'reviews_update_log'

    site_id = Column(Integer, default=0)
    goods_id = Column(Integer, default=0)
    goods_spu = Column(String(128), comment='商品SPU')
    goods_url = Column(String(255))
    log_date = Column(DateTime, comment='记录日期', default=datetime.now())
    # is_done = Column(Boolean, comment='是否已完成', default=0)

    @classmethod
    def get_log_by_spu(cls, site_id: int, spu: str):
        db_session = cls.get_db_session()
        return db_session.query(cls).filter(and_(
            cls.site_id == site_id,
            cls.goods_spu == spu,
        )).order_by(cls.created_at.desc()).first()

    # @classmethod
    # def done_log_by_id(cls, log_id: int):
    #     cls.save_update({'id': log_id}, {'is_done': 1})

    @classmethod
    def add_log(cls, goods_model: Goods):
        cls.save_create({'site_id': goods_model.site_id, 'goods_id': goods_model.id, 'goods_spu': goods_model.asin})

    @classmethod
    def is_exists_by_spu(cls, site_id: int, spu: str, expires_in=None) -> bool:
        log = cls.get_log_by_spu(site_id, spu)
        if log:
            print("---------is_exists_by_spu----true")
            print(log.id)
            if not expires_in:
                return True
            if time.time() - log.updated_at < expires_in:
                return True
        print("---------is_exists_by_spu----false")
        return False


