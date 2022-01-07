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

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = GoodsReviewAmazonItem()

        if cls.check_robot_happened(response):
            meta["item"] = item
            is_next = input("continue: <Enter yes>")
            if is_next.lower() != "yes":
                return False
            if "http_proxy_component" in meta:
                meta["http_proxy_component"].delete_proxy()
            yield Request(response.url, callback=cls.parse, meta=meta, dont_filter=True)

        page_ele = cls(response)
        reviews_num = page_ele.reviews_count
        total_page = int(reviews_num / 10) + 1
        eles = page_ele.elements
        db_session = GoodsReviewModel.get_db_session()
        is_review_too_old = False
        # {'sortBy': 'recent'}
        is_review_exists = False
        for ele in eles:
            review = GoodsReview(ele)
            review.spider = spider
            item['goods_id'] = goods_id
            item['goods_code'] = goods_code
            review_code = review.code
            item['code'] = review_code
            model = GoodsReviewModel.get_model(db_session, {'code': review_code, 'site_id': spider.site_id})
            if model:
                is_review_exists = True
            item['rating_value'] = review.rating_value
            item['title'] = review.title
            item['sku_text'] = review.sku_text
            item['body'] = review.body
            time_text = review.review_date
            print('=======time_text=======' + time_text)
            time_format = "%d %B %Y"
            if time_text.find("月") > -1:
                time_format = "%Y年%m月%d日"
            if time_text.find(", ") > -1:
                time_format = "%B %d, %Y"  # April 11, 2021 OR November 5, 2019
            if time_text.find(". ") > -1:
                time_format = "%d %B. %Y"  # 17. April 2020

            timestamp = mktime(strptime(time_text, time_format)) if time_text else 0
            old_time = int(time()) - REVIEWED_TIME_IN
            if 0 < timestamp < old_time:
                is_review_too_old = True
            item['review_time'] = timestamp  # 评论时间戳
            if timestamp:
                item['review_date'] = datetime.strptime(time_text, time_format)  # datetime.fromtimestamp(timestamp)
            item['time_str'] = time_text
            item['url'] = review.url
            item['color'] = review.color
            yield item

        print('===============total_page : ' + str(total_page))
        x_reviews = XReviews(spider)

        can_next_request = True
        check_exists = False # TODO is_review_exists 条件判断. 使用配置项。
        if page == total_page:
            can_next_request = False
        if is_review_too_old:
            can_next_request = False
        if check_exists and is_review_exists:
            can_next_request = False
        if can_next_request:
            # 仅取N个月内的评论
            next_page = page + 1
            print('=======current page:  ' + str(page) + '====next page : ' + str(next_page))
            next_url = x_reviews.get_reviews_url_by_asin(goods_code, next_page)
            yield Request(
                next_url,
                cls.parse,
                meta=dict(goods_id=goods_id, goods_code=goods_code, page=next_page, spider=spider, dont_filter=True)
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
        text = ""
        ele = self.element.xpath(XReviews.xpath_review_sku)
        if ele:
            tlist = ele.extract()
            text = "{}|{}".format(tlist[0], tlist[1]) if len(tlist) == 2 else tlist[0]
            # elex = ele.xpath('string(.)').extract()[0]
        return text

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
            if text.find(' vom ') > -1:
                # Rezension aus Deutschland vom 17. April 2020
                tt = text.split()
                return tt[1].strip()
        return ''

    @property
    def color(self):
        text = ""
        if self.sku_text:
            text = XReviews.get_color_in_sku_text(self.sku_text)
        return text

