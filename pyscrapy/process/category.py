from pyscrapy.items import GympluscoffeeCategoryItem
from pyscrapy.spiders import GympluscoffeeSpider
from pyscrapy.models import GoodsCategory
from .base import Base


class Gympluscoffee(Base):

    def process_item(self, item: GympluscoffeeCategoryItem, spider: GympluscoffeeSpider):
        db_session = self.db_session
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
