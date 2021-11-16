from pyscrapy.spiders import GympluscoffeeSpider
from pyscrapy.items import GympluscoffeeGoodsSkuItem
from pyscrapy.models import GoodsSku, GoodsSkuQuantityLog
import datetime
import time
import json
from .base import Base


def add_or_update_goods_quantity_log(model: GoodsSku, log_id: int, db_session):
    log: GoodsSkuQuantityLog = db_session.query(GoodsSkuQuantityLog).filter(
        GoodsSkuQuantityLog.log_id == log_id, GoodsSkuQuantityLog.sku_id == model.id).first()
    now_datetime = datetime.datetime.now()
    if log:
        log.quantity = model.inventory_quantity
        log.datetime = now_datetime
        print('UPDATE GoodsSkuQuantityLog id={}'.format(str(log.id)))
    else:
        log = GoodsSkuQuantityLog(
            log_id=log_id, goods_id=model.goods_id, sku_id=model.id,
            quantity=model.inventory_quantity, datetime=now_datetime)
        db_session.add(log)
        print('ADD GoodsSkuQuantityLog id={}'.format(str(log.id)))


class SkuGympluscoffee(Base):

    def process_item(self, item: GympluscoffeeGoodsSkuItem, spider: GympluscoffeeSpider):
        db_session = self.db_session
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
            attrs['updated_at'] = int(time.time())  # update方法无法自动更新时间戳
            db_session.query(GoodsSku).filter(GoodsSku.id == model.id).update(attrs)
        else:
            opt_str = 'SUCCESS ADD '
            model = GoodsSku(**attrs)
            db_session.add(model)
        add_or_update_goods_quantity_log(model, spider.log_id, db_session)
        db_session.commit()
        print(opt_str + ' GOODS SKU : ' + json.dumps(attrs))
