from urllib.parse import urlencode
import re
import json
from scrapy.http import TextResponse

BASE_URL = "https://www.amazon.com"


class GoodsListInRanking(object):
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

    xpath_goods_title = '//*[@id="productTitle"]/text()'
    xpath_goods_price_base = '//div[@class="a-section a-spacing-small"]//td/span[@class="a-price a-text-price a-size-base"]/span[1]/text()'
    xpath_goods_price = '//div[@class="a-section a-spacing-small"]//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span[1]/text()'
    xpath_goods_price_save = '//div[@class="a-section a-spacing-small"]//span[@class="a-color-price"]/span[@class="a-price a-text-price a-size-base"]/span[1]/text()'
    xpath_goods_detail_items = '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span/text()'
    xpath_goods_rank_detail = '//div[@id="detailBulletsWrapper_feature_div"]/ul[1]/li/span'
    xpath_goods_image = '//div[@id="imgTagWrapperId"]/img/@src'
    xpath_reviews_text = '//*[@id="acrCustomerReviewText"]/text()'
    re_goods_rank_num_cn = r"商品里排第(.+?)名"
    re_goods_rank_num_en = r"#(.+?) in "
    re_root_category_name_cn = r">查看商品销售排行榜(.+?)<"
    re_root_category_name_en = r">See Top 100 in (.+?)\)"  # (字符必加反斜杠转义符

    """
    Best Sellers Rank: #4,639 in Clothing, Shoes & Jewelry (See Top 100 in Clothing, Shoes & Jewelry)
        #2 in Men's Cycling Underwear
        #2 in Men's Cycling Shorts
    """

    @classmethod
    def get_rank_html(cls, response: TextResponse) -> str:
        rank_ele = response.xpath(cls.xpath_goods_rank_detail)
        if rank_ele:
            return response.xpath(cls.xpath_goods_rank_detail + '[contains(string(),"")]').get()
        return ''

    @classmethod
    def get_rank_num(cls, text: str) -> int:
        rank_info = re.findall(cls.re_goods_rank_num_cn, text)
        if not rank_info:
            rank_info = re.findall(cls.re_goods_rank_num_en, text)
            if not rank_info:
                return 0
        rank_text = rank_info[0]
        return int(rank_text.replace(',', ''))

    @classmethod
    def get_root_category_name(cls, text: str) -> str:
        info = re.findall(cls.re_root_category_name_cn, text)
        if not info:
            info = re.findall(cls.re_root_category_name_en, text)
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


class Common(object):

    BASE_URL = BASE_URL

    @staticmethod
    def get_url_by_code(code: str, params=None) -> str:
        if params:
            return "{}/dp/{}?{}".format(BASE_URL, code, urlencode(params))
        return "{}/dp/{}".format(BASE_URL, code)

    @staticmethod
    def get_code_by_goods_url(url: str) -> str:
        urls = url.split('/')
        index = urls.index('dp')
        return urls[index + 1]


class GoodsReviews(object):
    """
    商品评论解析类
    """

    reviews_url = BASE_URL + "/product-reviews/{}"
    reviews_url_more = reviews_url + '/ref=cm_cr_arp_d_paging_btm_next_{}?pageNumber={}'

    xpath_reviews_count = '//*[@id="filter-info-section"]/div/span/text()'

    xpath_reviews_items = '//div[@class="a-section review aok-relative"]'
    xpath_review_id = '@id'
    xpath_review_sku = 'div/div/div[3]/a'
    xpath_review_rating = 'div/div/div[2]/a[1]/@title'
    xpath_review_title = 'div/div/div[2]/a[2]/span/text()'
    xpath_review_url = 'div/div/div[2]/a[2]/@href'
    xpath_review_title_no_a = 'div/div/div[2]/span[2]/span[1]/text()'
    xpath_review_body = 'div/div/div[@class="a-row a-spacing-small review-data"]/span/span/text()'
    xpath_review_date = 'div//span[@class="a-size-base a-color-secondary review-date"]/text()'

    @classmethod
    def get_simple_reviews_url(cls, url, page=1):
        re_text = r"product-reviews/(.+?)/"
        urls = re.findall(re_text, url)
        asin = urls[0]
        result_url = cls.reviews_url.format(asin)
        if page > 1:
            page_str = str(page)
            result_url = cls.reviews_url_more.format(asin, page_str, page_str)
        return result_url

    @classmethod
    def get_reviews_url_by_asin(cls, asin, page=1, language='zh_CN') -> str:
        url = cls.reviews_url.format(asin) + "?language=" + language
        if page > 1:
            pgstr = str(page)
            url = cls.reviews_url_more.format(asin, pgstr, pgstr) + "&language=" + language
        return url

    @classmethod
    def get_color_in_sku_text(cls, sku, lang='cn'):
        lang_color = '颜色:'
        lang_size = '尺寸:'
        if lang == 'en':
            lang_color = 'Color:'
            lang_size = 'Size:'
        color_index = sku.find(lang_color)
        color = ''
        if color_index < 0:
            # 没有出现颜色
            return ''
        if color_index > 0:
            # 颜色不在起始位
            colors = sku.split(lang_color)
            color = colors[1].strip()
        if color_index == 0:
            # 颜色在起始位
            if sku.find(lang_size) < 0:
                colors = sku.split(lang_color)
                color = colors[1].strip()
            if sku.find(lang_size) > 0:
                colors = sku.split(lang_size)
                sku = colors[0].strip()
                colors = sku.split(lang_color)
                color = colors[1].strip()
        return color


class GoodsListInStore(object):

    re_config_json = "var config = {(.+?)}};\\n"

    @classmethod
    def get_config_json(cls, text: str) -> dict:
        info = re.findall(cls.re_config_json, text)
        if info:
            if len(info) == 2:
                if info[1].find("\"content\":{\"ASINList\":") > -1:
                    config_str = "{" + info[1] + "}}"
                    return json.loads(config_str)
        return {}

    @classmethod
    def get_asin_list(cls, text: str) -> list:
        config = cls.get_config_json(text)
        if config:
            return config['content']['ASINList']
        return []

