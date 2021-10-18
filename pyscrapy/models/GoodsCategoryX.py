from sqlalchemy import Column, String, Integer
from . import BaseModel, Goods, GoodsCategory
from sqlalchemy.orm.session import Session


class GoodsCategoryX(BaseModel):

    __tablename__ = 'goods_category_x'

    goods_id = Column(Integer, default=0)
    category_id = Column(Integer, default=0)

    @classmethod
    def save_goods_categories(cls, goods: Goods, categories: list, db_session: Session):
        for category in categories:
            attrs = {'goods_id': goods.id, 'category_id': category.id}
            x = db_session.query(cls).filter_by(**attrs).first()
            if not x:
                x = cls(**attrs)
                db_session.add(x)
                db_session.commit()
