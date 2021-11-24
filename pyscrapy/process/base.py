from pyscrapy.database import Database
from sqlalchemy.orm.session import Session
from Config import Config
from service import Singleton
from pyscrapy.models import Goods
from pyscrapy.spiders import BaseSpider


class Base(Singleton):

    db_session: Session

    def __init__(self):
        super().__init__()
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

    def get_real_model(self, attrs: dict, model: Goods, spider: BaseSpider):
        # 剔除重复的URL, 防止重复采集
        if model:
            return model
        if 'url' in attrs:
            model = self.db_session.query(Goods).filter(
                Goods.url == attrs["url"], Goods.site_id == spider.site_id
            ).first()
            if model:
                print('===Waring!!!====URL EXISTS===Skip=URL==: ' + attrs['url'])
        return model
