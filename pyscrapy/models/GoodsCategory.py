from sqlalchemy import Column, String, Integer
from . import BaseModel
from sqlalchemy.orm.session import Session


class GoodsCategory(BaseModel):

    __tablename__ = 'goods_category'

    site_id = Column(Integer, default=0)
    parent_id = Column(Integer, default=0)
    name = Column(String(64))
    url = Column(String(255))

    @classmethod
    def get_or_insert(cls, args: dict, db_session: Session):
        model = db_session.query(cls).filter_by(**args).first()
        if not model:
            model = cls(**args)
            db_session.add(model)
        return model
