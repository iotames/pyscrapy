from scrapy.http import TextResponse
from pyscrapy.extracts.amazon import GoodsReviews as XReviews, Common as XAmazon
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.items import GoodsReviewAmazonItem
from datetime import datetime
from time import strptime, mktime, time
from scrapy import Request
from pyscrapy.enum.spider import REVIEWED_TIME_IN
from pyscrapy.models import GoodsReview as GoodsReviewModel


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
        spider = meta['spider']
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
        db_session = GoodsReviewModel.get_db_session()
        is_review_too_old = False
        # is_review_exists = False
        for ele in eles:
            review = GoodsReview(ele)
            item['goods_id'] = goods_id
            item['goods_code'] = goods_code
            review_code = review.code
            item['code'] = review_code
            # model = GoodsReviewModel.get_model(db_session, {'code': review_code, 'site_id': spider.site_id})
            # if model:
            #     is_review_exists = True
            item['rating_value'] = review.rating_value
            item['title'] = review.title
            item['sku_text'] = review.sku_text
            item['body'] = review.body
            time_text = review.review_date
            # April 11, 2021 OR November 5, 2019 ...
            time_format = "%Y年%m月%d日" if time_text.find("月") > -1 else "%B %d, %Y"
            timestamp = mktime(strptime(time_text, time_format))
            old_time = int(time()) - REVIEWED_TIME_IN
            if timestamp < old_time:
                is_review_too_old = True
            item['review_time'] = timestamp  # 评论时间戳
            item['review_date'] = datetime.strptime(time_text, time_format)  # datetime.fromtimestamp(timestamp)
            item['time_str'] = time_text
            item['url'] = review.url
            item['color'] = review.color
            yield item

        print('===============total_page : ' + str(total_page))
        if (page < total_page) and (not is_review_too_old):  # and (not is_review_exists):
            # 仅取3个月内的评论
            next_page = page + 1
            print('=======current page:  ' + str(page) + '====next page : ' + str(next_page))
            next_url = XReviews.get_reviews_url_by_asin(goods_code, next_page)
            yield Request(
                next_url,
                cls.parse,
                meta=dict(goods_id=goods_id, goods_code=goods_code, page=next_page, spider=spider)
            )


class GoodsReview(BaseElement):

    BASE_URL = "https://www.amazon.com"

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
            if text.find('月') > -1:
                # 2021年11月23日 在美国审核
                tt = text.split(' ')
                return tt[0].strip()
            if text.find(' on ') > -1:
                # Reviewed in the United States on April 11, 2021
                tt = text.split(' on ')
                return tt[1].strip()
        return ''

    @property
    def color(self):
        sku_text = self.sku_text
        if sku_text:
            return XReviews.get_color_in_sku_text(sku_text)
        return ''

