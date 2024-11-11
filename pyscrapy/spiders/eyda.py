from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from scrapy.selector import Selector
from pyscrapy.items import BaseProductItem
from models import Product


class EydaSpider(BaseSpider):
    name = 'eyda'
    domain = "eyda.com"
    base_url = "https://eyda.com"
    group = "all"
    allowed_domains = ['eyda.com', "eyda.dk"]

    # 该属性cls静态调用 无法继承覆盖
    # custom_settings = {
    #     'DOWNLOAD_DELAY': 2,
    #     'RANDOMIZE_DOWNLOAD_DELAY': True,
    #     'DOWNLOAD_TIMEOUT': 30,
    #     'RETRY_TIMES': 5,
    #     'COOKIES_ENABLED': False,
    #     'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # default 8
    #     'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
    # }

    def __init__(self, name=None, **kwargs):
        super(EydaSpider, self).__init__(name=name, **kwargs)
        self.start_urls = [f"{self.base_url}/collections/{self.group}?page=0&view=data"]
    
    def get_price_text(self, price):
        if self.domain == "eyda.com":
            return f"€{price}"
        if self.domain == "eyda.dk":
            return f"{price} kr."

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, self.parse, meta=dict(page=1))

    def parse(self, response: TextResponse):
        # meta = response.meta
        # page = meta['page']
        goods_items_list = response.json()
        for item in goods_items_list:
            # published_at: "2021-01-28 11:44:14 +0100"

            desc_html = item['description']
            select = Selector(text=desc_html)
            composition_ele = select.xpath('//p[contains(text(), "% ")]')
            clen = len(composition_ele)
            composition_text = ""
            if clen > 0:
                if clen == 1:
                    composition_text = composition_ele[0].xpath("text()").get()
                else:
                    for com_ele in composition_ele:
                        text = com_ele.xpath("text()").get()
                        if len(text) < 50:
                            composition_text = text

            status = Product.STATUS_AVAILABLE if item['available'] else 0
            image = "https:" + item['images'][0]['src']
            price = item['price'] / 100
            spu = item['handle']
            url = self.get_site_url(f"/products/{spu}")
            code = item['id']
            title = item['title']
            category_name = item['type']
            colors_list = item['color_values'] if 'color_values' in item else []
            quantity = 0
            sku_info_list = []
            for sku_item in item['variants']:
                # sku title quantity price option1 option2 image
                quantity += sku_item['quantity']
                sku_info = {
                    'title': sku_item['title'],
                    'quantity': sku_item['quantity'],
                    'image': "https:" + sku_item['image'],
                    'price': sku_item['price'] / 100
                }
                sku_info_list.append(sku_info)
            details = {'composition_text': composition_text, 'colors_list': colors_list, 'sku_info_list': sku_info_list}
            goods_item = BaseProductItem()
            goods_item['status'] = status
            goods_item['spu'] = spu
            goods_item['spider_name'] = self.name
            goods_item['price'] = price
            goods_item["price_text"] = self.get_price_text(price)
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = code
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['category_name'] = category_name
            goods_item['quantity'] = quantity
            goods_item['detail'] = details
            yield goods_item
        # if response.status == 200 and goods_items_list:
        #     nextPage = page+1
        #     nextUrl = response.url.replace(f"page={str(page)}", f"page={str(nextPage)}")
        #     yield Request(nextUrl, self.parse, meta=dict(page=nextPage))

