import re
from scrapy.http import TextResponse


class GoodsRankingList(object):
    """
    商品排行榜数据解析类
    """

    xpath_goods_items = '//*[@id="zg-ordered-list"]/li/span/div/span'
    xpath_url = 'a/@href'
    xpath_goods_img = 'a/span/div/img/@src'
    xpath_goods_title = 'a/span/div/img/@alt'
    xpath_review = "div[@class='a-icon-row a-spacing-none']/a[2]"


class GoodsDetail(object):
    """
    商品详情数据解析类
    """

    xpath_goods_price = '//div[@class="a-section a-spacing-small"]//span[@class="a-price a-text-price a-size-medium apexPriceToPay"]/span[1]'
    xpath_goods_detail_items = '//ul[@class="a-unordered-list a-vertical a-spacing-mini"]/li/span'
    xpath_goods_rank_detail = '//div[@id="detailBulletsWrapper_feature_div"]/ul[1]/li/span'
    re_goods_rank_in_root = r"商品里排第(.+?)名"

    @classmethod
    def get_rank_num_in_root(cls, text: str) -> int:
        print('====get_rank_num_in_root=======================================')
        root_rank_info = re.findall(cls.re_goods_rank_in_root, text)
        print(root_rank_info)
        if not root_rank_info:
            return 0
        rank_text = root_rank_info[0]
        rank_num = int(rank_text.replace(',', ''))
        print(rank_num)
        return rank_num

    @classmethod
    def get_goods_rank_list(cls, response: TextResponse):
        print('======get_goods_rank_list============================')
        xpath_eles = cls.xpath_goods_rank_detail + '/ul/li'
        eles = response.xpath(xpath_eles)
        if not eles:
            return []
        data = []
        for ele in eles:
            rank_text = ele.xpath('span/text()').get().strip()  # 商品里排第19名
            category_text = ele.xpath('span/a/text()').get().strip()  # 女士运动裙裤
            url = ele.xpath('span/a/@href').get()  # /-/zh/gp/bestsellers/fashion/2211990011/ref=pd_zg_hrsr_fashion
            data.append({'rank_text': rank_text, 'category_text': category_text, 'url': url})
        return data

    @staticmethod
    def get_goods_detail_feature(contains, response: TextResponse):
        xpath_feature_key = '//*[@id="detailBullets_feature_div"]/ul/li/span/span[contains(text(), "{}")]'.format(
            contains)
        ele = response.xpath(xpath_feature_key + '/parent::span/span[2]')
        if ele:
            return ele.xpath('text()').get().strip()
        return ''

