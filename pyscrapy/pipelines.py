# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .spiders import GympluscoffeeSpider, StrongerlabelSpider
from pyscrapy.spiders.basespider import BaseSpider
from .items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, StrongerlabelGoodsItem, GympluscoffeeGoodsSkuItem
from .database import Database
from .models import Site, Goods, GoodsCategory, GoodsCategoryX, GoodsSku
from Config import Config
import scrapy
import json

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
                attrs = {'site_id': spider.site_id, 'parent_id': 0}
                url = item['url']
                if url.startswith('/'):
                    url = spider.base_url + url
                attrs['url'] = url
                attrs['name'] = item['name']

                if item['parent_url'] and item['parent_name']:
                    p_url = spider.base_url + item['parent_url']
                    p_name = item['parent_name']
                    p_model = db_session.query(GoodsCategory).filter(
                        GoodsCategory.site_id == spider.site_id,
                        GoodsCategory.name == p_name,
                        GoodsCategory.url == p_url
                    ).first()
                    if not p_model:
                        p_model = GoodsCategory(site_id=spider.site_id, name=p_name, url=p_url)
                        db_session.add(p_model)
                        db_session.commit()
                    attrs['parent_id'] = p_model.id

                model = item['model']
                if not model:
                    model = GoodsCategory(**attrs)
                    db_session.add(model)
                    db_session.commit()
                    print('SUCCESS save category ' + attrs['name'])
                else:
                    print('Skip category ' + attrs['name'])
                # spider.categories_info[model.name]['id'] = model.id

            if isinstance(item, GympluscoffeeGoodsItem):
                attrs = {'site_id': spider.site_id}
                for key, value in item.items():
                    if key == 'model':
                        continue
                    if key == 'url' and value.startswith('/'):
                        value = spider.base_url + value
                    attrs[key] = value

                model: Goods = item['model'] if 'model' in item else None
                if model:
                    opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
                    # for attr_key, attr_value in attrs.items():
                    #     setattr(model, attr_key, attr_value)
                    db_session.query(Goods).filter(Goods.id == model.id).update(attrs)  # 经常要更新多次 原因未知
                else:
                    opt_str = 'SUCCESS ADD '
                    model = Goods(**attrs)
                    db_session.add(model)
                db_session.commit()
                print(opt_str + ' GOODS : ' + json.dumps(attrs))

            if isinstance(item, GympluscoffeeGoodsSkuItem):
                attrs = {}
                for item_key, item_value in item.items():
                    if item_key == 'model':
                        continue
                    if item_key == 'options':
                        i = 1
                        for option_value in item_value:
                            attrs['option'+str(i)] = option_value
                            i += 1
                        continue
                    attrs[item_key] = item_value
                model: GoodsSku = item['model'] if 'model' in item else None
                if model:
                    opt_str = 'SUCCESS UPDATE '
                    # for attr_key, attr_value in attrs.items():
                    #     setattr(model, attr_key, attr_value)
                    db_session.query(GoodsSku).filter(GoodsSku.id == model.id).update(attrs)
                else:
                    opt_str = 'SUCCESS ADD '
                    model = GoodsSku(**attrs)
                    db_session.add(model)
                db_session.commit()
                print(opt_str + ' GOODS SKU : ' + json.dumps(attrs))

    def open_spider(self, spider):
        pass
