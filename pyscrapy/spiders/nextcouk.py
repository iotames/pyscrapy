from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem
import json
from models import Product


class NextcoukSpider(BaseSpider):
    # custom_settings = {
    #     'DOWNLOAD_DELAY': 1,
    #     'RANDOMIZE_DOWNLOAD_DELAY': True,
    #     'DOWNLOAD_TIMEOUT': 30,
    #     'RETRY_TIMES': 5,
    #     'COOKIES_ENABLED': False,
    #     'CONCURRENT_REQUESTS_PER_DOMAIN': 3, # default 8
    #     'CONCURRENT_REQUESTS': 6, # default 16 recommend 5-8
    # }
    name: str = 'nextcouk'
    limit: int = 12

    categories = [
        "women", # end of 13992
        # "men",
        ]

    def __init__(self, name=None, **kwargs):
        self.allowed_domains = ['www.next.co.uk', 'www2.next.co.uk']
        self.base_url = "https://www.next.co.uk"
        self.domain = "next.co.uk"
        super(NextcoukSpider, self).__init__(name=name, **kwargs)
	# s.OutputFields = []string{"Position", "Image", "Code", "Spu", "Group", "CollectedAt", "Title", "Price", "PriceText", "Rating", "Color", "VariantsNum", "Brand", "ReviewsNum", "Material", "Url", "Desc"}

    def request_items(self, category: str, start: int, meta=None) -> Request:
        urls_map = {
            "women": f"https://www.next.co.uk/products-fragment?criteria=www.next.co.uk%2Fshop%2Fgender-women-productaffiliation-clothing-0&providerArgs=_br_var_1&start={str(start)}&pagesize=12&contextid=uid%3D5771667307600:v%3D13.0:ts%3D1659686557298:hc%3D2&type=Category&fields=items&segment=&searchTerm=",
            "men": f"https://www.next.co.uk/products-fragment?criteria=www.next.co.uk%2Fshop%2Fgender-men-productaffiliation-clothing-0&providerArgs=_br_var_1&start={str(start)}&pagesize=12&contextid=uid%3D5771667307600:v%3D13.0:ts%3D1659686557298:hc%3D3&type=Category&fields=items&segment=&searchTerm=",
            # "women": f"{self.base_url}/shop/gender-women-productaffiliation-clothing/isort-score-minprice-0-maxprice-150000-srt-{str(start)}",
            # "men": f"{self.base_url}/shop/gender-men-productaffiliation-clothing/isort-score-minprice-0-maxprice-80000-srt-{str(start)}"
        }
        url = urls_map[category]
        if meta is None:
            meta=meta=dict(category=category)
        else:
            meta["category"] = category
        return Request(url, callback=self.parse_products, meta=meta)

    def start_requests(self):
        for category in self.categories:
            yield self.request_items(category, 0)
    
    def parse_products(self, response: TextResponse):
        meta = response.meta
        category = meta["category"]
        products_nodes = response.xpath("//article[@class=\"Item  Fashion  \"]")
        for ele in products_nodes:
            url = ele.xpath("//h2[@class=\"Title \"]/a/@href").extract()[0]
            url = self.get_site_url(url)
            title = ele.xpath("//h2[@class=\"Title \"]/a/@title").extract()[0]
            code = ele.xpath("@data-itemnumber").extract()[0]
            spu = ""
            url_split = url.split("/")
            if url_split[3] == "style":
                spu = url_split[4]
            else:
                spu = url_split[3]
            positionSrt = ele.xpath("@data-itemposition").extract()[0]
            position = int(positionSrt)
            color_text = ele.xpath("@data-colour").get()
            brand = ele.xpath("@data-brand").get()
            price_text = ele.xpath("//div[@class=\"Price\"]/a/text()").get().strip()
            price = 0.0
            if price_text != "":
                if price_text.find("-") > 1:
                    price_text = price_text.split("-")[0].strip()
                price = self.get_price_by_text(price_text)
            colorsNodes = ele.xpath("//ul[@class=\"Colours\"]/li")
            colors_num = 1
            len_colors = len(colorsNodes)
            if len_colors > 0:
                colors_num = len_colors
            image = ele.xpath("//a[@class=\"Image\"]/img/@src").get()
            rating_ele = ele.xpath("//div[contains(@class, \"Rating rating-\")]/@class")
            rating = 0
            if rating_ele:
                rating_split = rating_ele.get().split("-")
                rating_str = rating_split[1]
                rating = int(rating_str)
            product_item = BaseProductItem()
            product_item["code"] = code
            product_item["spu"] = spu
            product_item["price_text"] = price_text
            product_item["price"] = price
            product_item["url"] = url
            product_item["title"] = title
            product_item["category_name"] = category
            product_item["variants_num"] = colors_num
            product_item["image"] = image
            product_item["image_urls"] = [image]
            detail = {
                "Position": position,
                "ColorText": color_text,
                "Rating": rating,
                "Brand": brand
            }
            product_item["detail"] = detail
            if url.find("/shop/") > 1:
                continue
            model = self.db_session.query(Product).filter(Product.code == code, Product.site_id == self.site_id).first()
            if model:
                print("-----Skip--Product-----modelExists-------", model.url)
                continue
            yield Request(url, self.parse_detail, meta=dict(item=product_item))

        len_nodes = len(products_nodes)
        print("------nextcouk----parse_products------", len_nodes)
        # if len_nodes < self.limit:
        #     print(f"------nextcouk----parse_products---{len_nodes} < {self.limit}---")
        #     return
        current_url: str = response.url
        srt_split = current_url.split("-srt-")
        if len(srt_split) > 1:
            srt_str = srt_split[1]
            srt = int(srt_str)
            next_url = current_url.replace(f"start={srt_str}", f"start={str(srt+self.limit)}")
            print("next---Url:", next_url)
            yield Request(next_url, self.parse_products, meta=dict(category=category))


    def parse_detail(self, response: TextResponse, **kwargs):
        meta = response.meta
        item = meta.get("item")
        material = response.xpath("//div[@id=\"Composition\"]/text()").get()
        product_json = response.xpath("//script[@type=\"application/ld+json\"]/text()").get().strip()
        print("---parse_detail----product_json-----", product_json)
        product_schema = json.loads(product_json)
        desc = ""
        reviews_num = 0
        if "description" in product_schema:
            desc = product_schema["description"]
        if "aggregateRating" in product_schema:
            if "reviewCount" in product_schema["aggregateRating"]:
                reviews_num = product_schema["aggregateRating"]["reviewCount"]
        item["reviews_num"] = reviews_num
        detail = item["detail"]
        detail["Material"] = material
        detail["Desc"] = desc
        item["detail"] = detail
        yield item