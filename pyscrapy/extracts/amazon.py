from urllib.parse import urlencode
import re
from scrapy.http import TextResponse

BASE_URL = "https://www.amazon.com"


class GoodsRankingList(object):
    """
    商品排行榜数据解析类
    """

    # '/bestsellers/sporting-goods'  # 运动与户外用品销售排行榜
    # '/bestsellers/sporting-goods/706814011'  # 户外休闲销售排行榜
    # '/bestsellers/fashion/2371062011?language=zh_CN'  # 服装、鞋靴和珠宝饰品 - 网球服 销量排行榜
    # '/new-releases/fashion/2371062011'  # 服装、鞋靴和珠宝饰品 - 网球服 新品排行榜

    xpath_goods_items = '//*[@id="zg-ordered-list"]/li/span/div/span'
    xpath_url = 'a/@href'
    xpath_goods_img = 'a/span/div/img/@src'
    xpath_goods_title = 'a/span/div/img/@alt'
    xpath_review = "div[@class='a-icon-row a-spacing-none']/a[2]/text()"


class GoodsDetail(object):
    """
    商品详情数据解析类
    """

    xpath_goods_price = '//div[@class="a-section a-spacing-small"]//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span[1]/text()'
    xpath_goods_detail_items = '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span/text()'
    xpath_goods_rank_detail = '//div[@id="detailBulletsWrapper_feature_div"]/ul[1]/li/span'
    re_goods_rank_num = r"商品里排第(.+?)名"
    re_root_category_name = r">查看商品销售排行榜(.+?)<"

    @classmethod
    def get_rank_num(cls, text: str) -> int:
        print(text)
        rank_info = re.findall(cls.re_goods_rank_num, text)
        print(rank_info)
        if not rank_info:
            return 0
        rank_text = rank_info[0]
        return int(rank_text.replace(',', ''))

    @classmethod
    def get_root_category_name(cls, text: str) -> str:
        info = re.findall(cls.re_root_category_name, text)
        if not info:
            return ''
        return info[0]

    @classmethod
    def get_rank_num_in_root(cls, text: str) -> int:
        print('====get_rank_num_in_root=======================================')
        return cls.get_rank_num(text)

    @classmethod
    def get_goods_rank_list(cls, response: TextResponse) -> list:
        print('======get_goods_rank_list============================')
        xpath_eles = cls.xpath_goods_rank_detail + '/ul/li'
        eles = response.xpath(xpath_eles)
        if not eles:
            return []
        data = []
        for ele in eles:
            category_text = ele.xpath('span/a/text()').get().strip()  # 女士运动裙裤
            rank_text = ele.xpath('span/text()').get().strip()  # 商品里排第19名
            print(category_text)
            print(rank_text)
            url = ele.xpath('span/a/@href').get()  # /-/zh/gp/bestsellers/fashion/2211990011/ref=pd_zg_hrsr_fashion
            rank_data = {'rank_num': cls.get_rank_num(rank_text), 'rank_text': rank_text, 'category_text': category_text, 'url': url}
            data.append(rank_data)
        return data

    @staticmethod
    def get_goods_detail_feature(contains, response: TextResponse):
        xpath_feature_key = '//*[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(), "{}")]'.format(
            contains)
        ele = response.xpath(xpath_feature_key + '/parent::span/span[2]')
        if ele:
            return ele.xpath('text()').get().strip()
        return ''


class Goods(object):

    @staticmethod
    def get_url_by_code(code: str, params=None) -> str:
        if params:
            return "{}/dp/{}?{}".format(BASE_URL, code, urlencode(params))
        return "{}/dp/{}".format(BASE_URL, code)

    @staticmethod
    def get_code_by_url(url: str) -> str:
        urls = url.split('/')
        index = urls.index('dp')
        return urls[index+1]

    @staticmethod
    def get_site_url(url: str) -> str:
        if url.startswith('http'):
            return url
        if url.startswith('/'):
            return BASE_URL + url
        return BASE_URL + '/' + url


class GoodsReviews(object):
    """
    商品评论解析类
    """

    @staticmethod
    def get_simple_reviews_url(url, page=1):
        re_text = r"product-reviews/(.+?)/"
        urls = re.findall(re_text, url)
        asin = urls[0]
        result_url = BASE_URL + '/product-reviews/' + asin
        if page > 1:
            page_str = str(page)
            result_url = result_url + '/ref=cm_cr_arp_d_paging_btm_next_{}?pageNumber={}'.format(page_str, page_str)
        return result_url

