# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .spiders import GympluscoffeeSpider
from .items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem
from .database import Database
from .models import Site, Goods, GoodsSku, GoodsCategory
from Config import Config

db = Database(Config().get_database())
db.ROOT_PATH = Config.ROOT_PATH
db_session = db.get_db_session()


class PyscrapyPipeline:

    def process_item(self, item, spider):
        if isinstance(spider, GympluscoffeeSpider):
            if isinstance(item, GympluscoffeeCategoryItem):
                attrs = {
                    'name': item['name'],
                    'site_id': spider.site_id
                }
                model = db_session.query(GoodsCategory).filter_by(**attrs).first()
                if not model:
                    model = GoodsCategory(**attrs)
                    db_session.add(model)
                    db_session.commit()
                    print('SUCCESS save category')
                spider.categories_info[model.name]['id'] = model.id

            if isinstance(item, GympluscoffeeGoodsItem):
                title = item['goods_title']
                url = spider.base_url + item['goods_url']
                category_name = item['category_name']
                model = db_session.query(Goods).filter(Goods.url == url).first()
                attrs = {
                    'title': title,
                    'url': url,
                    'category_name': category_name,
                    'site_id': spider.site_id,
                    'category_id': spider.categories_info[category_name]['id']
                }
                if not model:
                    model = Goods(**attrs)
                    db_session.add(model)
                    db_session.commit()
                    print('SUCCESS save goods ' + title)

    def open_spider(self, spider):
        if isinstance(spider, GympluscoffeeSpider):
            site = db_session.query(Site).filter(Site.name == GympluscoffeeSpider.name).first()
            if not site:
                attrs = {
                    'name': GympluscoffeeSpider.name,
                    'domain': GympluscoffeeSpider.domain,
                    'home_url': GympluscoffeeSpider.base_url
                }
                site = Site(**attrs)
                db_session.add(site)
                db_session.commit()
            spider.site_id = site.id
