from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.items import BaseGoodsItem
from scrapy.http import TextResponse
from pyscrapy.extracts.shein import Common as XShein
from pyscrapy.models import GoodsCategory
from pyscrapy.extracts.shein import GoodsList as XGoodsList


class GoodsList(BasePage):

    @property
    def elements(self) -> list:
        return self.response.xpath(XGoodsList.xpath_items)

    @property
    def categories(self) -> list:
        return self.response.xpath(XGoodsList.xpath_categories)

    @classmethod
    def parse(cls, response: TextResponse):
        meta = response.meta
        page = meta['page'] if 'page' in meta else 1
        grab = cls(response)
        spider = meta['spider']
        categories_map = meta['categories_map'] if 'categories_map' in meta else None

        if 'only_category' in meta:
            for cat in grab.categories:
                ele = Categories(cat)
                dbs = GoodsCategory.get_db_session()
                cate_info = {'code': ele.cat_id, 'name': ele.cat_name, 'parent_code': ele.parent_id, 'site_id': spider.site_id}
                cmodel = GoodsCategory.get_model(dbs, cate_info)
                if not cmodel:
                    GoodsCategory.create_model(dbs, cate_info)
                dbs.commit()
                print(cate_info)
            return True

        goods_list = grab.elements
        print('===========goods_list=====len=' + str(len(goods_list)))
        for ele in goods_list:
            goods_ele = GoodsInList(ele)
            goods_ele.spider = spider
            goods_ele.page = page
            if not goods_ele.url:
                print('=====Skip======goods_url ======')
                continue
            goods_item = goods_ele.item
            goods_item["spider_name"] = spider.name
            goods_item["category_id"] = categories_map[goods_ele.category_code].id
            goods_item["category_name"] = categories_map[goods_ele.category_code].name
            yield goods_item
            # yield Request(url, callback=GoodsDetail.parse, meta=dict(item=goods_item, categories_map=categories_map))
        # if page == 1:
        #     yield Request(
        #         response.url.replace('pg=1', 'pg=2'),
        #         callback=cls.parse,
        #         meta=dict(page=2)
        #     )


class GoodsInList(BaseElement):

    page = 1

    @property
    def url(self) -> str:
        return self.get_url(self.get_text(XGoodsList.xpath_url))

    @property
    def category_code(self):
        return XShein.get_cat_id_by_url(self.url)

    @property
    def code(self):
        text = self.get_text(XGoodsList.xpath_goods_id)
        return text.split('-')[1]

    @property
    def rank_num(self) -> int:
        text = self.get_text(XGoodsList.xpath_goods_id)
        rank_in_page = int(text.split('-')[0]) + 1
        return rank_in_page + (self.page - 1)*120

    @property
    def title(self):
        return self.get_text(XGoodsList.xpath_title)

    @property
    def image(self):
        img_text = self.get_text(XGoodsList.xpath_image)
        return 'http:' + img_text if img_text else ''

    @property
    def item(self) -> BaseGoodsItem:
        goods_item = BaseGoodsItem()
        image = self.image

        goods_item["url"] = self.url
        goods_item["image"] = self.image
        goods_item["code"] = self.code
        goods_item["title"] = self.title
        goods_item["image_urls"] = [image]
        goods_item["details"] = {"rank_num": self.rank_num, "rank_score": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}
        return goods_item


class Categories(BaseElement):

    @property
    def cat_id(self):
        return self.get_text(XGoodsList.xpath_cat_id)

    @property
    def cat_name(self):
        return self.get_text(XGoodsList.xpath_cat_name)

    @property
    def parent_id(self):
        return self.get_text(XGoodsList.xpath_cat_parent_id)

