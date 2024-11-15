from pyscrapy.items import  BaseProductItem
from pyscrapy.spiders import BaseSpider
from models import Product, ProductQuantity
from datetime import datetime
from time import time, mktime
from .base import Base
from copy import copy


class ProcessProductBase(Base):

    def add_quantity(self, newprod: dict, before: Product):
        if before == None:
            return
        db_session = self.db_session
        qty_before = self.db_session.query(ProductQuantity).filter(ProductQuantity.product_id == before.id).order_by(ProductQuantity.id.desc()).first()
        # qty_before_unix = int(mktime(qty_before.created_at.timetuple()))
        # print(f"add_quantity----product_id({qty_before.product_id})--code({before.code})--{qty_before_unix}----{qty_before.unix_time}-")

        if qty_before:
            if (int(time()) - qty_before.unix_time) < 6*3600:
                print(f"Skip ADD Quantity--product_id({qty_before.product_id})--code({before.code})--qty_before.unix_time({qty_before.unix_time})---")
                return
        if (int(time()) - int(mktime(before.collected_at.timetuple()))) < 6*3600:
            print(f"Skip ADD Quantity--product_id({before.id})--code({before.code})--before.collected_at({before.collected_at})---")
            return
        qty_after = newprod.get("quantity")
        qty_diff = before.quantity - qty_after
        if qty_diff < 0:
            qty_diff = 0
        attrs = {
            "product_id": before.id,
            "time_before": before.collected_at,
            "quantity_before": before.quantity,
            "quantity_after": qty_after,
            "quantity_diff": qty_diff,
            "unix_time": int(time())
        }
        db_session.add(ProductQuantity(**attrs))
        db_session.commit()

    def process_item(self, item: BaseProductItem, spider: BaseSpider):
        if not spider.name or len(spider.name.strip()) == 0:
        # if 'spider_name' not in item:
            err_msg = 'process_item error: spider.name is empty!'
            print(err_msg)
            raise RuntimeError(err_msg)

        db_session = self.db_session
        not_update = ['image_urls', 'image_paths', 'model']
        attrs = {'site_id': spider.site_id, "collected_at": datetime.now()}
        for key, value in item.items():
            if key in not_update:
                if key == 'image_paths' and value:
                    attrs['local_image'] = value[0]
                continue
            attrs[key] = value

        model: Product = item['model'] if 'model' in item else None
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
            attrs['updated_at'] = datetime.now()  # update方法无法自动更新时间戳
            # CONCURRENT_REQUESTS （并发请求数） 值过小， 可能导致经常要更新多次的问题. 也可能是网址重复
            print(f"----beforeupdate--product--code({model.code})---{model.id}----{model.quantity}---{model.collected_at}----")
            prod_before = copy(model)
            db_session.query(Product).filter(Product.id == model.id).update(attrs)
            print(f"----afterupdate--product--code({model.code})---{model.id}----{model.quantity}---{model.collected_at}----")
            if "quantity" in item:
                self.add_quantity(attrs, prod_before)
        else:
            self.update_details(attrs)
            opt_str = 'SUCCESS ADD '
            model = Product(**attrs)
            db_session.add(model)

        db_session.commit()
        print(opt_str + ' GOODS :================SAVE SUCCESS=================')
        print(attrs)
