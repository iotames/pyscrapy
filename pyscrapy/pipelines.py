# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .spiders import GympluscoffeeSpider, StrongerlabelSpider
from pyscrapy.spiders.basespider import BaseSpider
from .items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, StrongerlabelGoodsItem
from .database import Database
from .models import Site, Goods, GoodsCategory
from Config import Config
import scrapy

db = Database(Config().get_database())
db.ROOT_PATH = Config.ROOT_PATH
db_session = db.get_db_session()


class PyscrapyPipeline:

    def process_item(self, item: scrapy.Item, spider):
        if isinstance(spider, StrongerlabelSpider):
            if isinstance(item, StrongerlabelGoodsItem):
                category_name = ''
                category_id = 0
                if item['categories']:
                    # TODO 一个商品属于多个类别
                    category_name = item['categories'][0]
                if category_name != '':
                    category_model = db_session.query(GoodsCategory).filter(
                        GoodsCategory.site_id == spider.site_id, GoodsCategory.name == category_name).first()
                    if category_model:
                        category_id = category_model.id
                    else:
                        category_model = GoodsCategory(name=category_name, site_id=spider.site_id)
                        db_session.add(category_model)
                # { in-stock: true, out-of-stock: false}
                status = Goods.STATUS_AVAILABLE
                # TODO stickers 包含多个标签 待发现
                if ('out-of-stock' in item['stickers']) and (item['stickers']['out-of-stock'] is True):
                    status = Goods.STATUS_SOLD_OUT
                attrs = {
                    'site_id': spider.site_id,
                    'code': item['code'],
                    'title': item['title'],
                    'url': item['url'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'image': item['image'],
                    'category_id': category_id,
                    'category_name': category_name,
                    'status': status
                }
                goods = db_session.query(Goods).filter(
                    Goods.code == item['code'], Goods.url == item['url']).first()
                if not goods:
                    goods = Goods(**attrs)
                    db_session.add(goods)
                    print('SUCCESS ADD GOODS')
                else:
                    db_session.query(Goods).filter(
                        Goods.code == item['code'], Goods.url == item['url']).update(attrs)
                    print('SUCCESS UPDATE GOODS')
                db_session.commit()

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
                else:
                    print('Skip goods ' + title)

    def open_spider(self, spider):
        if isinstance(spider, BaseSpider):
            site = db_session.query(Site).filter(Site.name == spider.name).first()
            if not site:
                attrs = {
                    'name': spider.name,
                    'domain': spider.domain,
                    'home_url': spider.base_url
                }
                site = Site(**attrs)
                db_session.add(site)
                db_session.commit()
            spider.site_id = site.id

    # def close_spider(self, spider):
    #     if isinstance(spider, GympluscoffeeSpider):
