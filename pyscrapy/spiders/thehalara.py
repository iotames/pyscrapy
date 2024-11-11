from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from scrapy.selector import Selector
from pyscrapy.items import BaseProductItem
from models import Product
import json


class Thehalara(BaseSpider):
    name = 'thehalara'
    domain = "thehalara.com"
    base_url = "https://thehalara.com"
    group = "best-sellers"
    allowed_domains = ['thehalara.com']

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
        super(Thehalara, self).__init__(name=name, **kwargs)
        self.start_urls = [
            f"{self.base_url}/collections/{self.group}?page=1"
        ]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, self.parse_items, meta=dict(page=1))

    def parse_items(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        print(f"page={page}----", response.url)
        items_nodes = response.xpath("//div[@class=\"site-box active box--small box--typo-small lap--box--small-lg box--center-align box--no-padding box--column-flow box__collection\"]")
        for n in items_nodes:
            url = n.xpath("div/a/@href").extract()[0].strip()
            url = self.get_site_url(url)
            print("--------detail------url="+url)
            image = n.xpath("div/a/div[@class=\"box--product-image primary\"]/img/@src").get().strip()
            image_split = image.split("?v=")
            if len(image_split) == 2:
                image = image_split[0]
            image = self.get_site_url(image)
            # title = n.xpath("//h3[@class=\"collectionTitle\"]/span/text()").strip()
            print(f"----pdetail----url:{url}--image:{image}----")
            code = n.xpath("div/a/div[@class=\"caption \"]/div//span[@id=\"getid\"]/@data-vid").get()
            spu = n.xpath("div/a/div[@class=\"caption \"]/div//span[@id=\"getid\"]/@data-colorful_pid").get()

            product_obj = n.xpath("div/a/div[@class=\"caption \"]/div//span[@class=\"productObj\"]/text()").get()
            p = json.loads(product_obj)
            title = p["title"]
            published_at = p["published_at"]  # "2022-03-31T16:58:34+08:00"
            vendor = p["vendor"]
            price = p["price"]/100
            original_price = 0
            if "compare_at_price" in p and p["compare_at_price"]:
                original_price = p["compare_at_price"]/100
            status = Product.STATUS_AVAILABLE if p['available'] else 0
            details = {
                "published_at": published_at,
                "vendor": vendor,
                "tags": p["tags"],
            }
            print(f"----------p--detail---title:{title}---price:{price}--original_price:{original_price}--status:{status}--")

            goods_item = BaseProductItem()
            goods_item['status'] = status
            goods_item['spu'] = spu
            goods_item['spider_name'] = self.name
            goods_item["original_price"] = original_price
            goods_item['price'] = price
            goods_item["price_text"] = f"${price}"
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['code'] = code
            goods_item['title'] = title
            goods_item['url'] = url
            # goods_item['category_name'] = category_name
            # goods_item['quantity'] = quantity
            goods_item['detail'] = details
            yield Request(url, self.parse_item, meta=dict(item=goods_item))

        if response.status == 200 and len(items_nodes) == 15:
            nextPage = page+1
            nextUrl = response.url.replace(f"page={page}", f"page={nextPage}")
            yield Request(nextUrl, self.parse_items, meta=dict(page=nextPage))

    
    def parse_item(self, response: TextResponse):
        meta = response.meta
        item = meta['item']

        color_eles = response.xpath("//select[@id=\"product-color\"]/option")
        url = response.xpath("//meta[@property=\"og:url\"]/@content").get()
        title = response.xpath("//meta[@property=\"og:title\"]/@content").get()
        materials_ele = response.xpath("//div[@class=\"krown-tabs\"]//p[contains(text(), \"Materials\")]/parent::div/ul[1]/li//span/text()")
        pjson = response.xpath("//script[@type=\"application/ld+json\"]/text()").get()
        skus_qty_eles = response.xpath("//select[@id=\"productSelect\"]/option")

        quantity = 0
        for sku_qty in skus_qty_eles:
            qty = sku_qty.xpath("@data-quantity").get()
            if qty:
                quantity += int(qty)

        materials_text = ""
        if materials_ele:
            materials = materials_ele.extract()
            for mt in materials:
                materials_text += mt.strip() + "|"

        p = json.loads(pjson)
        reviews_num = 0
        rating_value = 0
        if "aggregateRating" in p:
            reviews_num = p["aggregateRating"]["reviewCount"]
            rating_value = p["aggregateRating"]["ratingValue"]
        detail = item["detail"]
        detail["rating_value"] = float(rating_value)
        detail["materials_text"] = materials_text


        item["reviews_num"] = int(reviews_num)
        item["url"] = url
        item["title"] = title
        item["variants_num"] = len(color_eles)
        item["quantity"] = quantity
        item["detail"] = detail
        yield item

        
