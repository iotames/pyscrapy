import re
from scrapy.http import TextResponse

BASE_URL = "https://us.shein.com"


class Common(object):

    categories_map = {

    }

    re_goods_id_cat_id = r'-p-(.+?)-cat-(.+?).html'

    @classmethod
    def get_goods_id_by_url(cls, url: str):
        res = re.findall(cls.re_goods_id_cat_id, url)
        if res:
            return res[0][0]

    @classmethod
    def get_cat_id_by_url(cls, url: str):
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

    xpath_categories = '//section[@class="side-filter__item-content-ul side-filter__item-content-ul_indent"]'
    xpath_cat_name = 'label/span[@class="S-radio__label"]/text()'
    xpath_cat_id = 'label/@data-cat-id'
    xpath_cat_parent_id = 'label/@data-parent-id'

"""
<section role="option" class="side-filter__item-content-ul side-filter__item-content-ul_indent" style="display:none;">
    <label role="radio" tabindex="0" data-cat-id="2186" data-parent-id="2181" class="S-radio eBpntH S-radio_radio12 S-radio_normal">
        <span class="S-radio__input"><i class="S-radio__input-inner"></i></span>
        <span class="S-radio__label">
            Women Sports Sweatshirts
        </span>
        <input type="radio" tabindex="-1" value="2186" class="S-radio__input-origin">
    </label> <!----> <!---->
</section>
"""


class GoodsDetail(object):

    re_spu = r"\"spu\":\"(.+?)\","
    re_brand = r"\"brand\":\"(.+?)\""
    re_price = "\"price\":{(.+?)}},"
    re_product_intro_data = "productIntroData:(.+?),\\n"
    xpath_title = '//meta[@property="og:title"]/@content'

