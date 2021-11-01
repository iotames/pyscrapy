from pyscrapy.items import StrongerlabelGoodsItem, GympluscoffeeGoodsItem
from pyscrapy.spiders import StrongerlabelSpider, GympluscoffeeSpider
from pyscrapy.models import Goods, GoodsCategory, GoodsCategoryX, GoodsQuantityLog
import datetime
import time
import json
from .base import Base


class Strongerlabel(Base):

    def process_item(self, item: StrongerlabelGoodsItem, spider: StrongerlabelSpider):
        db_session = self.db_session
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
        if item['image_paths']:
            attrs['local_image'] = item['image_paths'][0]
        goods = db_session.query(Goods).filter(
            Goods.code == item['code'], Goods.url == url).first()
        opt_str = 'unknown'
        if not goods:
            goods = Goods(**attrs)
            db_session.add(goods)
            opt_str = 'ADD'
        else:
            opt_str = 'UPDATE'
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            db_session.query(Goods).filter(
                Goods.code == item['code'], Goods.url == url).update(attrs)

        goods_quantity_log = GoodsQuantityLog(
            log_id=spider.log_id, goods_id=goods.id, quantity=goods.quantity, datetime=datetime.datetime.now())
        db_session.add(goods_quantity_log)

        db_session.commit()
        print('SUCCESS {} GOODS {}'.format(opt_str, str(goods.id)))
        GoodsCategoryX.save_goods_categories(goods, categories, db_session)


class Gympluscoffee(Base):

    def process_item(self, item: GympluscoffeeGoodsItem, spider: GympluscoffeeSpider):
        db_session = self.db_session
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
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题
            db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
        else:
            opt_str = 'SUCCESS ADD '
            model = Goods(**attrs)
            db_session.add(model)
        goods_quantity_log = GoodsQuantityLog(
            log_id=spider.log_id, goods_id=model.id, quantity=model.quantity, datetime=datetime.datetime.now())
        db_session.add(goods_quantity_log)
        db_session.commit()
        print(opt_str + ' GOODS : ' + json.dumps(attrs))
