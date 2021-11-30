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

    @classmethod
    def parse(cls, response: TextResponse):
        # if cls.check_robot_happened(response):
        #     return False
        grab = cls(response)
        for ele in grab.elements:
            ele = GoodsInList(ele)
            url = ele.url
            if not url:
                continue
            goods_item = ele.item
            print(goods_item)
            yield goods_item
            # yield Request(url, callback=GoodsDetail.parse, meta=dict(item=goods_item))
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
        return XShein.get_category_id_by_url(self.url)

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

