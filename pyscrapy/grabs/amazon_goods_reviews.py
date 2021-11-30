from scrapy.http import TextResponse
from pyscrapy.extracts.amazon import GoodsReviews as XReviews, Common as XAmazon
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.items import GoodsReviewAmazonItem
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
        meta = response.meta
        goods_code = meta['goods_code']
        page = meta['page'] if 'page' in meta else 1
        goods_id = meta['goods_id'] if 'goods_id' in meta else 0
        if cls.check_robot_happened(response):
            return False

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = GoodsReviewAmazonItem()

        page_ele = cls(response)
        reviews_num = page_ele.reviews_count
        total_page = int(reviews_num / 10) + 1
        eles = page_ele.elements
        for ele in eles:
            review = GoodsReview(ele)
            item['goods_id'] = goods_id
            item['goods_code'] = goods_code
            item['code'] = review.code
            item['rating_value'] = review.rating_value
            item['title'] = review.title
            item['sku_text'] = review.sku_text
            item['body'] = review.body
            item['review_date'] = review.review_date
            item['url'] = review.url
            item['color'] = review.color
            yield item

        print('===============total_page : ' + str(total_page))
        if page < total_page:
            next_page = page+1
            print('=======current page:  ' + str(page) + '====next page : ' + str(next_page))
            next_url = XReviews.get_reviews_url_by_asin(goods_code, next_page)
            yield Request(
                next_url,
                cls.parse,
                meta=dict(goods_id=goods_id, goods_code=goods_code, page=next_page)
            )


class GoodsReview(BaseElement):

    @property
    def code(self):
        return self.get_text(XReviews.xpath_review_id)

    @property
    def title(self):
        title1 = self.get_text(XReviews.xpath_review_title)
        if title1:
            return title1
        return self.get_text(XReviews.xpath_review_title_no_a)

    @property
    def sku_text(self):
        ele = self.element.xpath(XReviews.xpath_review_sku)
        if ele:
            elex = ele.xpath('string(.)')
            if elex:
                return elex.extract()[0]  # .get()
        return self.get_text(XReviews.xpath_review_sku)

    @property
    def body(self):
        return self.get_text(XReviews.xpath_review_body)

    @property
    def rating_value(self):
        text = self.get_text(XReviews.xpath_review_rating)
        if text:
            return int(text.split('.')[0])
        return 0

    @property
    def url(self):
        return self.get_url(self.get_text(XReviews.xpath_review_url))

    @property
    def review_date(self):
        text = self.get_text(XReviews.xpath_review_date)
        if text:
            tt = text.split(' ')
            if len(tt) > 1:
                return tt[0].strip()
        return ''

    @property
    def color(self):
        sku_text = self.sku_text
        if sku_text:
            return XReviews.get_color_in_sku_text(sku_text)
        return ''

