from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
# from scrapy.selector import Selector
from pyscrapy.items import BaseProductItem


class Paragonfitwear(BaseSpider):
    name = 'paragonfitwear'
    domain = "www.paragonfitwear.com"
    base_url = "https://www.paragonfitwear.com"
    allowed_domains = ['www.paragonfitwear.com']

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        # 'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
    }

    def __init__(self, name=None, **kwargs):
        super(Paragonfitwear, self).__init__(name=name, **kwargs)
        self.start_urls = [
            f"{self.base_url}/collections/all?page=1"
        ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, self.parse_items, meta=dict(page=1))

    def parse_items(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        print(f"page={page}----", response.url)
        items_nodes = response.xpath("//div[@itemtype=\"http://schema.org/ItemList\"]/div")
        for n in items_nodes:
            goods_item = BaseProductItem()
            goods_item['status'] = 0
            goods_item['category_name'] = n.xpath("//span[@class=\"stamped-product-reviews-badge\"]/@data-product-type").get()
            goods_item['spu'] = n.xpath("//span[@class=\"stamped-product-reviews-badge\"]/@data-product-sku").get()
            goods_item["price_text"] = n.xpath("//span[@class=\"current_price\"]/text()").get()
            goods_item['image'] = 'https:'+n.xpath("//div[@class=\"image-element__wrap\"]/img/@data-src").get()
            # goods_item['image_urls'] = [image]
            goods_item['code'] = n.xpath("//span[@class=\"stamped-product-reviews-badge\"]/@data-id").get()
            goods_item['title'] = n.xpath("//span[@class=\"title\"]/text()").get().strip()
            goods_item['url'] = self.get_site_url(n.xpath("//a[@class=\"product-info__caption\"]/@href").extract()[0].strip())
            print("--------detail------url="+goods_item['url'])
            yield goods_item
            # yield Request(goods_item['url'], self.parse_item, meta=dict(item=goods_item))
        # if response.status == 200 and len(items_nodes) == 100:
        #     nextPage = page+1
        #     nextUrl = response.url.replace(f"page={page}", f"page={nextPage}")
        #     yield Request(nextUrl, self.parse_items, meta=dict(page=nextPage))
