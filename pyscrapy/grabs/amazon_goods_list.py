from pyscrapy.extracts.amazon import GoodsListInRanking as XRankingList, Common as XAmazon, GoodsListInStore as XStoreGoods
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.items import AmazonGoodsItem
from scrapy.http import TextResponse
from scrapy import Request
from time import sleep


class GoodsRankingList(BasePage):

    @property
    def elements(self) -> list:
        return self.response.xpath(XRankingList.xpath_goods_items)

    @classmethod
    def parse(cls, response: TextResponse):
        print('============goods_list==========1')
        if response.status == 404:
            print(response.text)
        if cls.check_robot_happened(response):
            is_next = input("continue: <Enter yes>")
            if is_next.lower() != "yes":
                return False
        print('============goods_list==========2')
        page = response.meta['page']
        grab = cls(response)
        rank_num = 1 if page == 1 else 51
        for ele in grab.elements:
            ele = GoodsInRankList(ele)
            url = ele.url
            print('===============goods_list==================3')
            print(ele.url)
            if not url:
                continue
            goods_item = ele.item
            goods_item["details"] = {'rank_num': rank_num}
            rank_num += 1
            yield goods_item
            # yield Request(url, callback=AmazonGoodsDetail.parse, meta=dict(item=goods_item), dont_filter=True)
        if page == 1:
            print('=========跳转太快第二页会没有数据==稍等3秒===')
            sleep(3)
            yield Request(
                response.url.replace('pg=1', 'pg=2'),
                callback=cls.parse,
                meta=dict(page=2),
                dont_filter=True
            )


class GoodsInRankList(BaseElement):

    BASE_URL = XAmazon.BASE_URL

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


class GoodsListInStore(BasePage):

    @classmethod
    def parse(cls, response: TextResponse):
        if cls.check_robot_happened(response):
            is_next = input("continue: <Enter yes>")
            if is_next.lower() != "yes":
                return False
        meta = response.meta
        merchant_id = meta['merchant_id']
        category_name = meta['category_name'] if 'category_name' in meta else ''
        asin_list = XStoreGoods.get_asin_list(response.text)
        print(asin_list)
        print(len(asin_list))
        if not asin_list:
            print('===================empty asin_list========' + response.url)
        for asin in asin_list:
            item = AmazonGoodsItem()
            item['merchant_id'] = merchant_id
            item['asin'] = asin
            item['code'] = asin
            if category_name:
                item['category_name'] = category_name
            yield Request(
                XAmazon.get_url_by_code(asin, {"language": 'zh_CN'}),
                # dont_filter=True, 不去掉重复的ASIN
                callback=AmazonGoodsDetail.parse,
                meta=dict(item=item)
            )


