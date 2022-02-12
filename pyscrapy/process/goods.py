from pyscrapy.items import StrongerlabelGoodsItem, GympluscoffeeGoodsItem, SweatybettyGoodsItem, AmazonGoodsItem, BaseGoodsItem
from pyscrapy.spiders import StrongerlabelSpider, GympluscoffeeSpider, SweatybettySpider, AmazonSpider, BaseSpider
from pyscrapy.models import Goods, GoodsCategory, GoodsCategoryX, GoodsQuantityLog, RankingGoods, GroupGoods
import datetime
import time
import json
from .base import Base
from pyscrapy.enum.spider import *
# from service.Singleton import Singleton


def add_or_update_goods_quantity_log(model: Goods, log_id: int, db_session):
    log: GoodsQuantityLog = db_session.query(GoodsQuantityLog).filter(
        GoodsQuantityLog.log_id == log_id, GoodsQuantityLog.goods_id == model.id).first()
    now_datetime = datetime.datetime.now()
    if log:
        log.quantity = model.quantity
        log.datetime = now_datetime
        print('UPDATE GoodsQuantityLog')
    else:
        goods_quantity_log = GoodsQuantityLog(
            log_id=log_id, goods_id=model.id, quantity=model.quantity, datetime=now_datetime)
        db_session.add(goods_quantity_log)
        print('ADD GoodsQuantityLog')


class GoodsStrongerlabel(Base):

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
            'status': item['status']
        }
        if 'image_paths' in item and item['image_paths']:
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

        add_or_update_goods_quantity_log(goods, spider.log_id, db_session)

        db_session.commit()
        print('SUCCESS {} GOODS {}'.format(opt_str, str(goods.id)))
        print(opt_str + ' GOODS : ' + json.dumps(attrs))
        GoodsCategoryX.save_goods_categories(goods, categories, db_session)


class GoodsGympluscoffee(Base):

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
            attrs[key] = value

        model: Goods = item['model'] if 'model' in item else None
        if model:
            self.update_details(attrs, model)
            opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
            # for attr_key, attr_value in attrs.items():
            #     setattr(model, attr_key, attr_value)
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题
            db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
        else:
            self.update_details(attrs)
            opt_str = 'SUCCESS ADD '
            model = Goods(**attrs)
            db_session.add(model)
        add_or_update_goods_quantity_log(model, spider.log_id, db_session)
        db_session.commit()
        print(opt_str + ' GOODS : ' + json.dumps(attrs))


class GoodsSweatybetty(Base):

    def process_item(self, item: SweatybettyGoodsItem, spider: SweatybettySpider):
        db_session = self.db_session
        not_update = ['image_urls', 'images', 'image_paths', 'model']
        attrs = {'site_id': spider.site_id}
        for key, value in item.items():
            if key in not_update:
                if key == 'image_paths' and value:
                    attrs['local_image'] = value[0]
                continue
            attrs[key] = value

        model: Goods = item['model'] if 'model' in item else None
        if model:
            self.update_details(attrs, model)
            opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
            # for attr_key, attr_value in attrs.items():
            #     setattr(model, attr_key, attr_value)
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题
            db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
        else:
            self.update_details(attrs)
            opt_str = 'SUCCESS ADD '
            model = Goods(**attrs)
            db_session.add(model)
        add_or_update_goods_quantity_log(model, spider.log_id, db_session)
        db_session.commit()
        print(opt_str + ' GOODS : ' + json.dumps(attrs))


class GoodsAmazon(Base):

    def process_item(self, item: AmazonGoodsItem, spider: AmazonSpider):
        db_session = self.db_session
        not_update = ['image_urls', 'images', 'image_paths', 'model']
        attrs = {'site_id': spider.site_id}
        for key, value in item.items():
            if key in not_update:
                if key == 'image_paths' and value:
                    attrs['local_image'] = value[0]
                continue
            attrs[key] = value

        model: Goods = item['model'] if 'model' in item else None

        if model is None:
            if 'code' in attrs:
                model = self.get_real_model_by_code(attrs['code'], spider)
            else:
                if 'url' in attrs:
                    model = self.get_real_model_by_url(attrs['url'], spider)

        if model:
            self.update_details(attrs, model)
            opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
            # for attr_key, attr_value in attrs.items():
            #     setattr(model, attr_key, attr_value)
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题
            db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
        else:
            self.update_details(attrs)
            opt_str = 'SUCCESS ADD '
            model = Goods(**attrs)
            db_session.add(model)
        db_session.commit()
        print(opt_str + ' GOODS : ' + json.dumps(attrs))
        if spider.ranking_log_id:
            GoodsBase.save_ranking_goods(model, spider)
        if spider.group_log_id:
            GoodsBase.save_group_goods(model, spider)


class GoodsBase(Base):

    def process_item(self, item: BaseGoodsItem, spider: BaseSpider):
        if 'spider_name' not in item:
            err_msg = 'process_item error: spider_name not in BaseGoodsItem!!!'
            print(err_msg)
            raise RuntimeError(err_msg)

        db_session = self.db_session
        not_update = ['image_urls', 'image_paths', 'model', 'spider_name']
        attrs = {'site_id': spider.site_id}
        for key, value in item.items():
            if key in not_update:
                if key == 'image_paths' and value:
                    attrs['local_image'] = value[0]
                continue
            attrs[key] = value

        model: Goods = item['model'] if 'model' in item else None
        # 剔除重复的URL, 防止重复采集
        if model is None:
            if 'code' in attrs:
                model = self.get_real_model_by_code(attrs['code'], spider)
            else:
                if 'url' in attrs:
                    model = self.get_real_model_by_url(attrs['url'], spider)

        if model:
            self.update_details(attrs, model)
            opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
            # for attr_key, attr_value in attrs.items():
            #     setattr(model, attr_key, attr_value)
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题. 也可能是网址重复
            db_session.query(Goods).filter(Goods.id == model.id).update(attrs)
        else:
            self.update_details(attrs)
            opt_str = 'SUCCESS ADD '
            model = Goods(**attrs)
            db_session.add(model)
        if 'quantity' in attrs:
            add_or_update_goods_quantity_log(model, spider.log_id, db_session)
        db_session.commit()
        print(opt_str + ' GOODS :================SAVE SUCCESS=================')
        print(attrs)

        # 添加或更新goods和ranking_log对应关系
        if spider.ranking_log_id:
            self.save_ranking_goods(model, spider)
        if spider.group_log_id:
            self.save_group_goods(model, spider)

    @staticmethod
    def save_ranking_goods(model: Goods, spider: BaseSpider):
        if spider.spider_child == CHILD_GOODS_LIST_ALL_COLORS:
            return False
        details = json.loads(model.details)
        rank_num = details['rank_num'] if 'rank_num' in details else 0
        spu = details['spu'] if 'spu' in details else ''
        spu = spu if spu else model.asin
        xd_find = {'site_id': spider.site_id, 'ranking_log_id': spider.ranking_log_id, 'goods_id': model.id}
        print(xd_find)

        xgoods = RankingGoods.get_self(xd_find)
        update_data = {
            # 'spider_run_log_id': spider.log_id,
            'goods_code': model.code,
            'rank_num': rank_num,
            'goods_spu': spu,
            'reviews_num': model.reviews_num,
            'goods_title': model.title,
            'goods_url': model.url
        }
        if xgoods:
            # 更新goods和ranking_log对应关系
            RankingGoods.save_update(xd_find, update_data)
        else:
            # 添加goods和ranking_log对应关系
            xd_find.update(update_data)
            RankingGoods.save_create(xd_find)

    @staticmethod
    def save_group_goods(model: Goods, spider: BaseSpider):
        if spider.spider_child == CHILD_GOODS_LIST_ALL_COLORS:
            return False
        details = json.loads(model.details)
        rank_num = details['group_rank_num'] if 'group_rank_num' in details else 0  # TODO
        spu = details['spu'] if 'spu' in details else ''
        spu = spu if spu else model.asin
        xd_find = {'site_id': spider.site_id, 'group_log_id': spider.group_log_id, 'goods_id': model.id}
        print(xd_find)

        xgoods = GroupGoods.get_self(xd_find)
        update_data = {
            # 'spider_run_log_id': spider.log_id,
            'goods_code': model.code,
            'rank_num': rank_num,
            'goods_spu': spu,
            'reviews_num': model.reviews_num,
            'goods_title': model.title,
            'goods_url': model.url
        }
        if xgoods:
            # 更新goods和group_log对应关系
            GroupGoods.save_update(xd_find, update_data)
        else:
            # 添加goods和group_log对应关系
            xd_find.update(update_data)
            GroupGoods.save_create(xd_find)
