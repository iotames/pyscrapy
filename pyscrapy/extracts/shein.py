import re
from scrapy.http import TextResponse

BASE_URL = "https://us.shein.com"


class Common(object):

    re_goods_id_cat_id = r'-p-(.+?)-cat-(.+?).html'

    @classmethod
    def get_goods_id_by_url(cls, url: str):
        res = re.findall(cls.re_goods_id_cat_id, url)
        if res:
            return res[0][0]

    @classmethod
    def get_category_id_by_url(cls, url: str):
        res = re.findall(cls.re_goods_id_cat_id, url)
        if res:
            return res[0][1]


class GoodsList(object):

    BASE_URL = BASE_URL

    xpath_items = '//section[@role="main"]/div/section'

    xpath_goods_id = '@data-expose-id'  # 0-2914948
    xpath_title = '@aria-label'  # 4pcs High Waist Scrunch Butt Sports Shorts
    xpath_url = 'div/a/@href'  # /4pcs-High-Waist-Scrunch-Butt-Sports-Shorts-p-2914948-cat-2188.html
    xpath_image = 'div/a/img/@data-src'  # //img.ltwebstatic.com/images3_pi/2021/07/07/1625658046e142483019056f402f5428741d1b0fdd_thumbnail_405x552.jpg


class GoodsDetail(object):

    re_spu = r"\"spu\":\"(.+?)\","

