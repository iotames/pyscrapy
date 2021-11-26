from pyscrapy.items import GoodsReviewAmazonItem
from pyscrapy.spiders import AmazonSpider
from pyscrapy.models import GoodsReview
from .base import Base
import json


class ReviewAmazon(Base):

    def process_item(self, item: GoodsReviewAmazonItem, spider: AmazonSpider):
        db_session = self.db_session
        site_id = spider.site_id
        model = None
        if 'code' in item:
            model = db_session.query(GoodsReview).filter(
                GoodsReview.code == item['code'], GoodsReview.site_id == site_id).first()
        attrs = {'site_id': site_id}
        for key, value in item.items():
            attrs[key] = value
        if model:
            opt_str = 'SUCCESS UPDATE id = {} : '.format(str(model.id))
            db_session.query(GoodsReview).filter(GoodsReview.id == model.id).update(attrs)
        else:
            opt_str = 'SUCCESS ADD '
            model = GoodsReview(**attrs)
            db_session.add(model)
        db_session.commit()
        print(opt_str + ' GOODS REVIEW : ' + json.dumps(attrs))



