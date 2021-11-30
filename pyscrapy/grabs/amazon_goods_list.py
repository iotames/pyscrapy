from pyscrapy.extracts.amazon import GoodsRankingList as XRankingList, Common as XAmazon
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.items import AmazonGoodsItem
from scrapy.http import TextResponse
from scrapy import Request


class GoodsRankingList(BasePage):

    @property
    def elements(self) -> list:
        return self.response.xpath(XRankingList.xpath_goods_items)

    @classmethod
    def parse(cls, response: TextResponse):
        if cls.check_robot_happened(response):
            return False
        grab = cls(response)
        rank_in = 1
        for ele in grab.elements:
            ele = GoodsInRankList(ele)
            url = ele.url
            if not url:
                continue
            goods_item = ele.item
            goods_item["details"] = {'rank_in': rank_in}
            rank_in += 1
            yield Request(url, callback=AmazonGoodsDetail.parse, meta=dict(item=goods_item))
        if response.meta['page'] == 1:
            yield Request(
                response.url.replace('pg=1', 'pg=2'),
                callback=cls.parse,
                meta=dict(page=2)
            )


class GoodsInRankList(BaseElement):

    @property
    def url(self) -> str:
        url_ele = self.element.xpath(XRankingList.xpath_url)
        if not url_ele:
            return ''
        url = url_ele.get().strip()
        url = self.get_url(url)
        return url

    @property
    def reviews_num(self):
        ele = self.element.xpath(XRankingList.xpath_review)
        if not ele:
            return 0
        review_text = ele.get()
        return int(review_text.replace(',', ''))

    @property
    def code(self):
        return XAmazon.get_code_by_goods_url(self.url)

    @property
    def item(self) -> AmazonGoodsItem:
        goods_item = AmazonGoodsItem()
        url = self.url
        image = self.element.xpath(XRankingList.xpath_goods_img).get()
        goods_item["url"] = url
        goods_item["image"] = image
        goods_item["code"] = self.code
        goods_item["title"] = self.element.xpath(XRankingList.xpath_goods_title).get()
        goods_item["reviews_num"] = self.reviews_num
        goods_item["image_urls"] = [image]
        return goods_item

