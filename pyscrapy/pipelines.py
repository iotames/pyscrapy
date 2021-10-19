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
from .models import Site, Goods, GoodsCategory, GoodsCategoryX
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
                categories = []

                if item['categories']:
                    # 一个商品属于多个类别
                    category_name = item['categories'][0]
                    for ctg_name in item['categories']:
                        ctg_args = {'name': ctg_name, 'site_id': spider.site_id}
                        category_model = GoodsCategory.get_or_insert(ctg_args, db_session)
                        categories.append(category_model)
                if categories:
                    category_name = categories[0].name
                    category_id = categories[0].id

                # { in-stock: true, out-of-stock: false}
                status = Goods.STATUS_AVAILABLE
                # TODO stickers 包含多个标签 待发现
                if ('out-of-stock' in item['stickers']) and (item['stickers']['out-of-stock'] is True):
                    status = Goods.STATUS_SOLD_OUT
                # 替换 findify.bogus 域名
                url: str = item['url']
                if url.startswith('https://findify.bogus'):
                    url = url.replace('findify.bogus', 'www.strongerlabel.com')
                attrs = {
                    'site_id': spider.site_id,
                    'code': item['code'],
                    'title': item['title'],
                    'url': url,
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'image': item['image'],
                    'category_id': category_id,
                    'category_name': category_name,
                    'status': status
                }
                goods = db_session.query(Goods).filter(
                    Goods.code == item['code'], Goods.url == url).first()
                opt_str = 'unknown'
                if not goods:
                    goods = Goods(**attrs)
                    db_session.add(goods)
                    opt_str = 'ADD'
                else:
                    opt_str = 'UPDATE'
                    db_session.query(Goods).filter(
                        Goods.code == item['code'], Goods.url == url).update(attrs)
                db_session.commit()
                print('SUCCESS {} GOODS {}'.format(opt_str, str(goods.id)))
                GoodsCategoryX.save_goods_categories(goods, categories, db_session)

        if isinstance(spider, GympluscoffeeSpider):
            if isinstance(item, GympluscoffeeCategoryItem):
                attrs = {
                    'name': item['name'],
                    'site_id': spider.site_id,
                    'url': item['url']
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
        pass
