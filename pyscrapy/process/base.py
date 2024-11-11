# from pyscrapy.database import Database
from service.DB import DB
from sqlalchemy.orm.session import Session
from service import Config
from service import Singleton
from models import Product
from pyscrapy.spiders import BaseSpider
import json


class Base(Singleton):

    db_session: Session

    def __init__(self):
        super().__init__()
        db = DB.get_instance(Config.get_database())
        self.db_session = db.get_db_session()

    def get_real_model_by_url(self, url: str, spider: BaseSpider):
        # 剔除重复的URL, 防止重复采集
        model = self.db_session.query(Product).filter(
            Product.url == url, Product.site_id == spider.site_id
        ).first()
        if model:
            print('===Waring!!!====URL EXISTS===Skip=URL==: ' + url)
        return model

    def get_real_model_by_code(self, code: str, spider: BaseSpider):
        # 剔除重复的商品code, 防止重复采集
        model = self.db_session.query(Product).filter(Product.code == code, Product.site_id == spider.site_id).first()
        if model:
            print(f"===Waring!!!====Goods code EXISTS===Skip=code={code}")
        return model

    @staticmethod
    def update_details(attrs: dict, model=None):
        if 'detail' in attrs:
            if model:
                detail = {}
                if model.detail:
                    detail = json.loads(model.detail)
                detail.update(attrs['detail'])
                attrs['detail'] = json.dumps(detail)
            if not model:
                attrs['detail'] = json.dumps(attrs['detail'])

