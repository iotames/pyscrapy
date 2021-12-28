from scrapy.http import TextResponse
from pyscrapy.extracts.amazon import GoodsDetail as XDetail, Common as XAmazon
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import AmazonGoodsItem
from scrapy import Request


class AmazonGoodsDetail(BasePage):

    __rank_html = None

    @property
    def image(self):
        return self.get_text(XDetail.xpath_goods_image)

    @property
    def asin_list(self):
        return self.response.xpath('//div[@id="variation_color_name"]/ul/li/@data-defaultasin').extract()

    @property
    def reviews_num(self) -> int:
        text = self.get_text(XDetail.xpath_reviews_text)
        if text:
            info = text.split(' ')
            if len(info) == 2:
                return int(info[0].replace(',', ''))
        return 0

    @property
    def title(self):
        return self.get_text(XDetail.xpath_goods_title)

    @property
    def price_text(self) -> str:
        print('=========price_text===' + self.get_text(XDetail.xpath_goods_price))
        return self.get_text(XDetail.xpath_goods_price)

    @property
    def price(self):
        return self.get_price_by_text(self.price_text)

    @property
    def price_base(self):
        text = self.get_text(XDetail.xpath_goods_price_base)
        return self.get_price_by_text(text)

    @property
    def price_save(self):
        return self.get_price_by_text(self.get_text(XDetail.xpath_goods_price_save))

    @property
    def details_items(self) -> list:
        items = []
        for ele in self.response.xpath(XDetail.xpath_goods_detail_items):
            detail_text = ele.get().strip()
            if detail_text:
                items.append(detail_text)
        return items

    @property
    def rank_html(self) -> str:
        if self.__rank_html is not None:
            return self.__rank_html
        self.__rank_html = XDetail.get_rank_html(self.response)
        return self.__rank_html

    @property
    def rank_list(self) -> list:
        if self.rank_html:
            return XDetail.get_goods_rank_list(self.response)
        return []

    @property
    def root_category_name(self) -> str:
        if self.rank_html:
            return XDetail.get_root_category_name(self.rank_html)
        return ''

    @property
    def root_category_rank_num(self) -> int:
        if self.rank_html:
            return XDetail.get_rank_num_in_root(self.rank_html)
        return 0

    @property
    def asin(self) -> str:
        return XDetail.get_goods_detail_feature('ASIN', self.response)

    @property
    def sale_at_text(self) -> str:
        text = XDetail.get_goods_detail_feature('上架时间', self.response)
        if not text:
            text = XDetail.get_goods_detail_feature('Date First Available', self.response)  # November 1, 2021
        return text

    @classmethod
    def parse(cls, response: TextResponse):
        meta = response.meta
        spider = meta['spider'] if 'spider' in meta else None
        dont_image = meta['dont_image'] if 'dont_image' in meta else False

        if 'item' in meta:
            item = response.meta['item']
        else:
            item = AmazonGoodsItem()

        if cls.check_robot_happened(response):
            meta["item"] = item
            is_next = input("continue: <Enter yes>")
            if is_next.lower() != "yes":
                return False
            if "http_proxy_component" in meta:
                meta["http_proxy_component"].delete_proxy()
            yield Request(response.url, callback=cls.parse, meta=meta, dont_filter=True)

        ele = cls(response)
        item['code'] = XAmazon.get_code_by_goods_url(response.url)
        item['url'] = response.url
        item['title'] = ele.title
        item['reviews_num'] = ele.reviews_num
        item['price_text'] = ele.price_text
        item['price'] = ele.price

        if ele.asin:
            item['asin'] = ele.asin

        if ('image' not in item) and (not dont_image):
            image = ele.image
            item['image'] = image
            item['image_urls'] = [image]

        details = {}
        if 'details' in item:
            details = item['details']

        details['items'] = ele.details_items
        details['price_base'] = ele.price_base
        details['price_save'] = ele.price_save
        details['sale_at'] = ele.sale_at_text
        details['asin'] = ele.asin if 'asin' not in item else item['asin']
        details['rank_list'] = ele.rank_list
        details['root_rank'] = ele.root_category_rank_num
        details['root_category_name'] = ele.root_category_name
        item['details'] = details
        print('=============parse_goods_detail=============end===========')
        print(item)
        yield item

        if spider:
            if spider.spider_child == 'goods_list_all_colors':
                code_list = ele.asin_list
                if 'goods_model' in meta:
                    gid = meta['goods_model'].id
                    print('==========code_list====goods_id={}=====asin_list={}'.format(str(gid), str(len(code_list))))
                    for code in code_list:
                        print('==========code_list====goods_id={}=====asin={}'.format(str(gid), code))
                        url = XAmazon.get_url_by_code(code, {"language": 'zh_CN'})
                        print('==================goods_url = ' + url)
                        yield Request(url, callback=AmazonGoodsDetail.parse, meta=dict(spider=spider))
        if 'next_request' in meta:
            yield meta['next_request']

