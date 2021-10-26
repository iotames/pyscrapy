# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import time

from itemadapter import ItemAdapter
from scrapy.settings import Settings
from .spiders import GympluscoffeeSpider, StrongerlabelSpider
from .items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem, StrongerlabelGoodsItem, GympluscoffeeGoodsSkuItem
from .database import Database
from .models import Site, Goods, GoodsCategory, GoodsCategoryX, GoodsSku
from Config import Config
from scrapy import Item, Request
import json
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
import hashlib
from scrapy.utils.python import to_bytes
import os

db = Database(Config().get_database())
db.ROOT_PATH = Config.ROOT_PATH
db_session = db.get_db_session()


class PyscrapyPipeline:

    def process_item(self, item: Item, spider):
        print('====================== PyscrapyPipeline : process_item ===================')
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

            if isinstance(item, GympluscoffeeGoodsItem):
                not_update = ['image_urls', 'images', 'image_paths', 'model']
                attrs = {'site_id': spider.site_id}
                for key, value in item.items():
                    if key in not_update:
                        if key == 'image_paths' and value:
                            attrs['local_image'] = value[0]
                        continue
                    if key == 'url' and value.startswith('/'):
                        value = spider.base_url + value
                    if key == 'details':
                        value = json.dumps(value)
                    attrs[key] = value

                model: Goods = item['model'] if 'model' in item else None
                if model:
                    opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
                    # for attr_key, attr_value in attrs.items():
                    #     setattr(model, attr_key, attr_value)
                    attrs['updated_at'] = int(time.time())
                    # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题
                    db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
                else:
                    opt_str = 'SUCCESS ADD '
                    model = Goods(**attrs)
                    db_session.add(model)
                db_session.commit()
                print(opt_str + ' GOODS : ' + json.dumps(attrs))

            if isinstance(item, GympluscoffeeGoodsSkuItem):
                attrs = {}
                not_update = ['image_urls', 'images', 'image_paths', 'model']
                for item_key, item_value in item.items():
                    if item_key in not_update:
                        if item_key == 'image_paths' and item_value:
                            attrs['local_image'] = item_value[0]
                        continue
                    if item_key == 'options':
                        i = 1
                        for option_value in item_value:
                            attrs['option' + str(i)] = option_value
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


class ImagePipeline(ImagesPipeline):
    
    # def process_item(self, item, spider):
    #     if isinstance(item, GympluscoffeeGoodsImageItem):
    #         return super(ImagePipeline, self).process_item(item, spider)

    @staticmethod
    def get_guid_by_url(url: str) -> str:
        return hashlib.sha1(to_bytes(url)).hexdigest()

    def file_path(self, request, response=None, info: ImagesPipeline.SpiderInfo = None, *, item=None):
        print('=========================file_path=====================')
        # print(item)
        image_guid = self.get_guid_by_url(request.url)
        return f'{info.spider.name}/{image_guid}.jpg'

    @classmethod
    def get_local_file_path_by_url(cls, url, spider):
        settings: Settings = spider.settings
        dir_path = settings.get('IMAGES_STORE') + os.path.sep + spider.name
        return dir_path + os.path.sep + cls.get_guid_by_url(url) + ".jpg"

    def get_media_requests(self, item, info: ImagesPipeline.SpiderInfo):
        print('================get_media_requests==========')
        urls = ItemAdapter(item).get(self.images_urls_field, [])  # item['image_urls']
        spider = info.spider
        # return [Request(u) for u in urls]
        for image_url in urls:
            file_path = self.get_local_file_path_by_url(image_url, spider)
            if os.path.isfile(file_path):
                print('SkipUrl: {} Exists File {}'.format(image_url, file_path))
                continue
            yield Request(image_url)

    def item_completed(self, results, item, info: ImagesPipeline.SpiderInfo):
        print('================item_completed==========')
        # results [] or [(True, {'url': '', 'path': 'dir/file.jpg', 'checksum': '', 'status': 'uptodate'})]
        image_paths = [x['path'] for ok, x in results if ok]
        adapter = ItemAdapter(item)
        # self.images_urls_field = 'image_urls'
        urls_field = self.images_urls_field
        if not image_paths and urls_field in item:
            image_paths = []
            for url in item[urls_field]:
                file_path = self.get_local_file_path_by_url(url, info.spider)
                if os.path.isfile(file_path):
                    image_paths.append(info.spider.name + os.path.sep + self.get_guid_by_url(url) + '.jpg')
        if not image_paths:
            raise DropItem("Item contains no images")
        adapter['image_paths'] = image_paths
        return item
