# from pyscrapy.database import Database
from service.DB import DB
from sqlalchemy.orm.session import Session
from Config import Config
from service import Singleton
from pyscrapy.models import Goods
from pyscrapy.spiders import BaseSpider
import json


class Base(Singleton):

    db_session: Session

    def __init__(self):
        super().__init__()
        # db = Database(Config().get_database())
        db = DB.get_instance(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

    def get_real_model_by_url(self, url: str, spider: BaseSpider):
        # 剔除重复的URL, 防止重复采集
        model = self.db_session.query(Goods).filter(
            Goods.url == url, Goods.site_id == spider.site_id
        ).first()
        if model:
            print('===Waring!!!====URL EXISTS===Skip=URL==: ' + url)
        return model

    def get_real_model_by_code(self, code: str, spider: BaseSpider):
        # 剔除重复的商品code, 防止重复采集
        model = self.db_session.query(Goods).filter(
            Goods.code == code, Goods.site_id == spider.site_id
        ).first()
        if model:
            print(f"===SKIP====Goods code EXISTS===code({code})")
        return model

    @staticmethod
    def update_details(attrs: dict, model=None):
        if 'details' in attrs:
            if model:
                details = {}
                if model.details:
                    details = json.loads(model.details)
                details.update(attrs['details'])
                attrs['details'] = json.dumps(details)
            if not model:
                attrs['details'] = json.dumps(attrs['details'])

