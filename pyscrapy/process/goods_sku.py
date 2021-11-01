from pyscrapy.spiders import GympluscoffeeSpider
from pyscrapy.items import GympluscoffeeGoodsSkuItem
from pyscrapy.models import GoodsSku, GoodsSkuQuantityLog
import datetime
import time
import json
from .base import Base


class Gympluscoffee(Base):

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
        sku_quantity_log = GoodsSkuQuantityLog(
            log_id=spider.log_id, goods_id=model.goods_id, sku_id=model.id,
            quantity=model.inventory_quantity, datetime=datetime.datetime.now())
        db_session.add(sku_quantity_log)
        db_session.commit()
        print(opt_str + ' GOODS SKU : ' + json.dumps(attrs))
