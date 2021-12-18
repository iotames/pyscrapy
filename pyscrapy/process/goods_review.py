from pyscrapy.items import GoodsReviewAmazonItem, GoodsReviewSheinItem
from pyscrapy.spiders import AmazonSpider, SheinSpider, BaseSpider
from pyscrapy.models import GoodsReview
from .base import Base
import json
from scrapy import Item


class BaseReview(Base):

    def process_item(self, item: Item, spider: BaseSpider):
        db_session = self.db_session
        site_id = spider.site_id
        model = None

        attrs = {'site_id': site_id}
        for key, value in item.items():
            if key == 'model':
                model = value
                print('=================review model is exists=======')
                continue
            attrs[key] = value
        if not model and ('code' in item):
            model = db_session.query(GoodsReview).filter(
                GoodsReview.code == item['code'], GoodsReview.site_id == site_id).first()
        if model:
            opt_str = 'SUCCESS UPDATE GOODS REVIEW id = {} : '.format(str(model.id))
            db_session.query(GoodsReview).filter(GoodsReview.id == model.id).update(attrs)
        else:
            opt_str = 'SUCCESS ADD GOODS REVIEW'
            model = GoodsReview(**attrs)
            db_session.add(model)
        db_session.commit()
        print(opt_str)
        print(attrs)


class ReviewAmazon(BaseReview):

    def process_item(self, item: GoodsReviewAmazonItem, spider: AmazonSpider):
        super(ReviewAmazon, self).process_item(item, spider)


class ReviewShein(BaseReview):

    def process_item(self, item: GoodsReviewSheinItem, spider: SheinSpider):
        super(ReviewShein, self).process_item(item, spider)




