from scrapy.http import TextResponse
from pyscrapy.extracts.amazon import GoodsReviews as XReviews
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import GoodsReviewItem
from pyscrapy.models import Goods as GoodsModel
from scrapy import Request


class AmazonGoodsReviews(BasePage):

    __reviews_count_text = None

    @property
    def elements(self) -> list:
        return self.response.xpath(XReviews.xpath_reviews_items)

    @property
    def count_text(self) -> str:
        if self.__reviews_count_text is None:
            self.__reviews_count_text = ''
            ele = self.response.xpath(XReviews.xpath_reviews_count)
            if ele:
                self.__reviews_count_text = ele.get().strip()
        return self.__reviews_count_text

    @property
    def rating_count(self) -> int:
        num = 0
        if self.count_text:
            text = self.count_text.split('|')[0]
            num = int(text.split(' ')[0].replace(',', ''))
        return num

    @property
    def reviews_count(self) -> int:
        num = 0
        if self.count_text:
            text = self.count_text.split('|')[1]
            num = int(text.split(' ')[1].replace(',', ''))
        return num

    @classmethod
    def parse(cls, response: TextResponse):
        if cls.check_robot_happened(response):
            return False
        meta = response.meta

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = GoodsReviewItem()

        page = meta['page'] if 'page' in meta else 1
        # if 'page' in meta:
        #     page = meta['page']

        goods_id = meta['goods_id'] if 'goods_id' in meta else 0
        # if 'goods_id' in meta:
        #     goods_id = meta['goods_id']

        page_ele = cls(response)
        reviews_num = page_ele.reviews_count
        total_page = int(reviews_num / 10) + 1
        eles = page_ele.elements
        for ele in eles:
            item['goods_id'] = goods_id
            rating_ele = ele.xpath(XReviews.xpath_reviews_rating)
            rating_value = 0
            if rating_ele:
                rating_value = int(rating_ele.get().split('.')[0])
            title = ''
            title_ele = ele.xpath(XReviews.xpath_reviews_title)
            if title_ele:
                title = title_ele.get().strip()
            sku_text = ''
            sku_ele = ele.xpath(XReviews.xpath_reviews_sku)
            if sku_ele:
                sku_text = sku_ele.get().strip()
            body = ''
            body_ele = ele.xpath(XReviews.xpath_review_body)
            if body_ele:
                body = body_ele.get().strip()
            # TODO 封装 ele 判断和获取text
            url = ''
            url_ele = ele.xpath(XReviews.xpath_reviews_url)
            if url_ele:
                url = url_ele.get().strip()
            color = ''
            if sku_text:
                color = XReviews.get_color_in_sku_text(sku_text)
            review_time = ''
            item['rating_value'] = rating_value
            item['title'] = title
            item['sku_text'] = sku_text
            item['body'] = body
            print(item)
            yield item
        if page < total_page:
            asin = meta['asin']
            next_url = XReviews.get_reviews_url_by_asin(asin, (page+1))
            yield Request(
                next_url,
                cls.parse,
                meta=dict(goods_id=goods_id, asin=asin)
            )


