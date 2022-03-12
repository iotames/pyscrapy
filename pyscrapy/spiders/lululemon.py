import re
from urllib.parse import urlencode
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.grabs.basegrab import BaseElement
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config

from pyscrapy.enum.spider import NAME_LULULEMON


class LululemonSpider(BaseSpider):
    """
    us.shein.com 露露柠檬电商平台
    """

    name = NAME_LULULEMON

    base_url = "https://shop.lululemon.com"

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    goods_list_urls = [
        '/api/c/women',  # 换行前,少了个逗号,导致的BUG. 不易发现
        '/api/c/men',
    ]

    xpath_reviews_num = '//span[@class="reviews-link__count"]/text()'  # ' (89)'
    xpath_details_list = '//div[@class="accordion-3Usrq accordionLarge-1hCr9"]/div'
    xpath_detail_title = 'h3/span/span/text()'
    # xpath_detail_items = 'div/div/div/div/ul/li/span/text()'

    def __init__(self, name=None, **kwargs):
        super(LululemonSpider, self).__init__(name=name, **kwargs)
        self.domain = "shop.lululemon.com"
        self.base_url = "https://shop.lululemon.com"
        self.allowed_domains = [self.domain]

    def request_goods_list(self, page: int, page_size: int, url_path: str):
        url = f"{self.get_site_url(url_path)}?{urlencode(dict(page=page, page_size=page_size))}"
        print(f"-------------request-url: {url}")
        return Request(
            url,
            callback=self.parse_goods_list,
            headers=dict(referer=self.base_url + "/"),
            meta=dict(page=page, page_size=page_size, url_path=url_path)
        )

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for url_path in self.goods_list_urls:
                yield self.request_goods_list(1, 9, url_path)

        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time()
            if self.app_env == self.spider_config.ENV_PRODUCTION:
                before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id, or_(
                    Goods.status == Goods.STATUS_UNKNOWN,
                    Goods.updated_at < before_time)
            )).all()
            goods_list_len = len(self.goods_model_list)
            print('=======goods_list_len============ : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield Request(self.get_site_url(model.url), headers={'referer': self.base_url + "/"},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        page_size = meta['page_size']  # 9 or 45
        url_path = meta['url_path']  # '/api/c/women' or '/api/c/men'

        next_page = page + 1
        next_page_size = page_size
        can_next = False
        if page_size == 9 and page == 5:
            next_page = 2
            next_page_size = 45
            can_next = True

        json_response = json.loads(response.text)

        links = json_response['links']  # first last next prev self
        self_page = int(links['self'].split('=')[1])  # self: "/c/men?page=3"
        last_page = int(links['last'].split('=')[1])  # self: "/c/men?page=11"
        if self_page < last_page:
            next_page = int(links['next'].split('=')[1])
            can_next = True

        print('===========next url===={}===page={}==page_size={}=='.format(url_path, str(page), str(page_size)))

        data = json_response['data']
        attributes = data['attributes']
        main_content = attributes['main-content']
        goods_list = []
        for main in main_content:
            if main['type'] == "CDPResultsList":
                goods_list = main["records"]
        for info in goods_list:
            price = info['list-price'][0]
            currency = info['currency-code']
            color_list = info['color-group']
            details = {
                'color_num': len(color_list),
                'color_list': color_list
            }
            image = info['sku-sku-images'][0] + "?wid=320"
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['code'] = info['unified-id']
            goods_item['asin'] = info['repository-id']  # prod10020121
            goods_item['title'] = info['display-name']
            goods_item['price'] = price
            goods_item['price_text'] = price + currency
            goods_item['url'] = self.get_site_url(info['pdp-url'])
            goods_item['category_name'] = info['parent-category-unified-id']
            goods_item['details'] = details
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            yield goods_item
        if can_next:
            yield self.request_goods_list(next_page, next_page_size, url_path)

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        # availableQuantity 库存
        print('====parse_goods_detail====goods_id={}===='.format(str(model.id)))

        # status = self.statuses[status_text] if status_text in self.statuses else Goods.STATUS_UNKNOWN
        reviews_num = 0
        reviews_num_text = response.xpath(self.xpath_reviews_num).extract()
        if reviews_num_text:
            reviews_num_text = reviews_num_text[0].strip()
            info = re.findall(r"\((.+?)\)", reviews_num_text)
            if info and info[0]:
                reviews_num = int(info[0])
        details_list = []
        details = json.loads(model.details)
        materials_list = []
        eles = response.xpath(self.xpath_details_list)
        for elee in eles:
            ele = BaseElement(elee)
            # TODO  Material and care 有2个条目
            div_eles = elee.xpath('div/div/div/div')
            i = 0
            for div_item in div_eles:
                ele_title = ele.get_text(self.xpath_detail_title)
                i += 1
                if i > 1:
                    ele_items = div_item.xpath('ul/li/span/text()').extract()
                    if ele_items:
                        ele_title += ":" + div_item.xpath('div/text()').extract()[0]
                        details_list.append({'title': ele_title, 'items': ele_items})
                if i == 1 and len(div_eles) == 1:
                    ele_items = div_item.xpath('ul/li/span/text()').extract()
                    if ele_items:
                        details_list.append({'title': ele_title, 'items': ele_items})
                if i == 1 and len(div_eles) > 1:
                    title_child = div_item.xpath('div/text()').extract()[0].strip()  # Materials
                    ele_title += ":" + title_child
                    if title_child.lower() == "materials":
                        ele_materials = div_item.xpath('ul/li/span/dl')
                        for material_ele in ele_materials:
                            material_title = material_ele.xpath('dt/text()').get().strip()
                            material_value = material_ele.xpath('dd/text()').get()
                            materials_list.append({'title': material_title.replace(':', ''), 'value': material_value})

        details['details_list'] = details_list
        details['materials_list'] = materials_list
        goods_item = BaseGoodsItem()
        goods_item['model'] = model
        goods_item['spider_name'] = self.name
        goods_item['reviews_num'] = reviews_num
        goods_item['details'] = details
        yield goods_item

