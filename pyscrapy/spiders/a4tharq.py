from models import UrlRequest, UrlRequestSnapshot
from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem, FromPage
import json
import re


class A4tharqSpider(BaseSpider):
    name = "4tharq"
    base_url = "https://4tharq.com"
    allowed_domains = ["4tharq.com"]
    start_urls = ["https://4tharq.com/collections/all"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        # 'FEED_URI': '4tharq.csv',
        # 'FEED_FORMAT': 'csv',
        # 'FEED_EXPORT_FIELDS': ['Thumbnail', 'Category', 'Title',  'Color', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url']
    }

    def start_requests(self):
        for requrl in self.start_urls:
            print('------start_requests----', requrl)
            # mustin = ['step', 'page', 'group', 'FromKey']
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1, step=1, group=1, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        # self.logger.debug(f"---------parse_list--page={page}---")
        self.lg.debug(f"-------parse_list---requrl:{response.url}--page={page}--")

        if 'dl' in meta:
            # print("------Skiped------parse_list---", response.url, page)
            self.lg.debug(f"----Skiped------parse_list--requrl:{response.url}--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            nds = response.xpath('//ul[@id="product-grid"]/li')
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                # 使用相对路径
                img = nd.xpath('.//img[@class="motion-reduce"]/@src').get()
                dd['Thumbnail'] = self.get_site_url(img)
                
                url = nd.xpath('.//a[@class="full-unstyled-link"]/@href').get()
                dd['Url'] = self.get_site_url(url)
                
                title = nd.xpath('.//span[@class="card-information__text h5"]/text()').get()
                dd['Title'] = title.strip() if title else None
                
                color = nd.xpath('.//span[@class="card-information__text card-information__colour"]/text()').get()
                dd['Color'] = color.strip() if color else None
                
                old_price_text = nd.xpath('.//span[@class="price-item price-item--regular"]/text()').get()
                dd['OldPriceText'] = old_price_text.strip() if old_price_text else None
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None
                
                price_text = nd.xpath('.//span[@class="price-item price-item--sale price-item--last"]/text()').get()
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                dd['image_urls'] = [dd['Thumbnail']]
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)

            nextPageUrl = ""
            next_page = response.xpath('//a[@aria-label="Next page"]/@href').get()
            if next_page:
                nextPageUrl = self.get_site_url(next_page)
            dl = {'ProductList': prods, 'NextPageUrl': nextPageUrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        
        for dd in prods:
            # yield dd
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        
        if dl['NextPageUrl'] != "":
            print(f"------------next_page-{dl['NextPageUrl']}---")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=dict(page=page+1, step=meta['step'], group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_detail(self, response: TextResponse):
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            self.lg.debug(f"----Skiped------parse_detail--requrl:{response.url}----dd:{dd}-")
            yield dd
            return
        # 解析 _BISConfig.product 后面的 JSON 数据
        script_text = response.xpath('//script[contains(text(), "_BISConfig.product")]/text()').get()
        if script_text:
            # 使用正则表达式提取 JSON 数据
            json_match = re.search(r'_BISConfig\.product\s*=\s*({.*?});', script_text, re.DOTALL)
            if json_match:
                product_json_str = json_match.group(1)
                try:
                    product_data = json.loads(product_json_str)
                    dd['Category'] = product_data.get('type')
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON data: {e}")

        try:
            # 解析 inventory_quantity 信息
            inventory_quantities = re.findall(r'_BISConfig\.product\.variants\[(\d+)\]\[\'inventory_quantity\'\]\s*=\s*(-?\d+);', script_text)
            total_inventory = sum(int(qty) for _, qty in inventory_quantities)
            dd['TotalInventoryQuantity'] = total_inventory
        except Exception as e:
            dd['TotalInventoryQuantity'] = 0
            # raise e
        
        sizelist = []
        for sz in response.xpath('//input[@name="Size"]/@value').getall():
            sizelist.append(sz)
        dd["SizeList"] = sizelist
        lensz = len(sizelist)
        if lensz == 0:
            lensz = 1
        dd['SizeNum'] = lensz
        # 提取面料信息
        fabric_info = response.xpath('//span[@class="description"]/p[strong[contains(text(), "Fabric Composition:")]]/following-sibling::p[1]/text()').get()
        dd['Material'] = fabric_info.strip() if fabric_info else None
        # print("-----------parse_detail--------", dd)
        self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
        yield dd