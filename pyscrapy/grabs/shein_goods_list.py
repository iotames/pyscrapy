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
        page = response.meta['page']
        grab = cls(response)
        categories_map = {}
        for cat in grab.categories:
            ele = Categories(cat)
            # print('=========each category:===')
            cate_info = {'cat_id': ele.cat_id, 'cat_name': ele.cat_name, 'parent_id': ele.parent_id}
            # print(cate_info)
            if ele.cat_id not in categories_map:
                categories_map[ele.cat_id] = cate_info
        goods_list = grab.elements
        print('===========goods_list=====len=' + str(len(goods_list)))
        print(categories_map)
        if not categories_map:
            print('categories_map is empty')
            return False
        for ele in goods_list:
            goods_ele = GoodsInList(ele)
            goods_ele.page = page
            url = goods_ele.url
            print('=====shein_goods_list======goods_url ======  ' + url)
            if not url:
                continue
            goods_item = goods_ele.item
            # yield goods_item
            yield Request(url, callback=GoodsDetail.parse, meta=dict(item=goods_item, categories_map=categories_map))
        # if page == 1:
        #     yield Request(
        #         response.url.replace('pg=1', 'pg=2'),
        #         callback=cls.parse,
        #         meta=dict(page=2)
        #     )


class GoodsInList(BaseElement):

    BASE_URL = XGoodsList.BASE_URL

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
    def rank_in(self) -> int:
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
        goods_item["spider_name"] = "shein"
        goods_item["url"] = self.url
        goods_item["image"] = self.image
        goods_item["code"] = self.code
        goods_item["title"] = self.title
        goods_item["image_urls"] = [image]
        goods_item["details"] = {"rank_in": self.rank_in, "rank_score": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}
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

