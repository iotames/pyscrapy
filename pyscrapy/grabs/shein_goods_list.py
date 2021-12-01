from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.items import BaseGoodsItem
from scrapy.http import TextResponse
from pyscrapy.extracts.shein import Common as XShein
from scrapy import Request
from pyscrapy.grabs.shein_goods import GoodsDetail
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
        # if cls.check_robot_happened(response):
        #     return False
        grab = cls(response)
        categories_map = {}
        for cat in grab.categories:
            ele = Categories(cat)
            if ele.cat_id not in categories_map:
                categories_map[ele.cat_id] = {'cat_id': ele.cat_id, 'cat_name': ele.cat_name, 'parent_id': ele.parent_id}
        goods_list = grab.elements
        print('===========goods_list=====len=' + str(len(goods_list)))
        countgoods = 0
        for ele in goods_list:
            ele = GoodsInList(ele)
            url = ele.url
            print('goods_url ======  ' + url)
            if not url:
                continue
            countgoods += 1
            print('=========countgoods = ' + str(countgoods))
            goods_item = ele.item
            # print(goods_item)
            # yield goods_item
            # print('==============next request===========' + url)
            yield Request(url, callback=GoodsDetail.parse, meta=dict(item=goods_item, categories_map=categories_map, count=countgoods))
        # if response.meta['page'] == 1:
        #     yield Request(
        #         response.url.replace('pg=1', 'pg=2'),
        #         callback=cls.parse,
        #         meta=dict(page=2)
        #     )


class GoodsInList(BaseElement):

    BASE_URL = XGoodsList.BASE_URL

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
        goods_item["spider_name"] = "shein"
        goods_item["url"] = self.url
        goods_item["image"] = self.image
        goods_item["code"] = self.code
        goods_item["title"] = self.title
        goods_item["image_urls"] = [image]
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

