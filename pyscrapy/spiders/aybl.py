from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
import json
import re

class AyblSpider(BaseSpider):
    name = "aybl"
    base_url = "https://www.aybl.com"
    allowed_domains = ["www.aybl.com"]
    start_urls = ["https://www.aybl.com/collections/all-products"]


    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'Category', 'Title',  'Color', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'aybl.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }


    def start_requests(self):
        self.page_size = 24
        for requrl in self.start_urls:
            print('------start_requests----', requrl)
            # mustin = ['step', 'page', 'group', 'FromKey']
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1, step=1, group=1, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        self.lg.debug(f"-------parse_list---requrl:{response.url}--page={page}--")

        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            # 1. 获取当前页所有商品
            nds = response.xpath('//product-list/product-card')
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                # 使用相对路径
                img = nd.xpath('.//img/@src').get()
                dd['Image'] = self.get_site_url(img)
                dd['Thumbnail'] = dd['Image'].replace('width=2000', 'width=200')
                
                url = nd.xpath('.//span[@class="product-card__title"]/a/@href').get()
                dd['Url'] = self.get_site_url(url)
                
                title = nd.xpath('.//span[@class="product-card__title"]/a/text()').get()
                dd['Title'] = title.strip() if title else None

                color = nd.xpath('.//span[@class="product-card__title product-title-color"]/text()').get()
                dd['Color'] = color.strip() if color else None
                
                old_price_text = nd.xpath('.//compare-at-price/span[@class="money"]/text()').get()
                dd['OldPriceText'] = old_price_text.strip() if old_price_text else None
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None
                
                price_text = nd.xpath('.//sale-price/span[@class="money"]/text()').get()   
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                dd['image_urls'] = [dd['Thumbnail']]
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            nextPageUrl = ""
            next_page = response.xpath('//a[@class="button load-more-button"]/@href').get()
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
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:
            # 获取标题 <h1 class="product-info__title h2" >Empower Seamless Leggings</h1>
            dd['Title'] = response.xpath('//h1[@class="product-info__title h2"]/text()').get()
            # 获取颜色 <p class="product-color">Black</p>
            dd['Color'] = response.xpath('//p[@class="product-color"]/text()').get()
            self.lg.debug(f"------parse_detail---title({dd['Title']})--color({dd['Color']})--")
            
            # 解析 _BISConfig.product 后面的 JSON 数据: <script id="back-in-stock-helper-embedded"> js something </script>
            script_text = response.xpath('//script[@id="back-in-stock-helper-embedded"]/text()').get()
            # script_text = response.xpath('//script[contains(text(), "_BISConfig.product")]/text()').get()
            if script_text:
                # 使用正则表达式提取 JSON 数据: _BISConfig.product = {"id":6862653096034};
                json_match = re.search(r'_BISConfig\.product = ({.*?});', script_text, re.DOTALL)
                if json_match:
                    product_json_str = json_match.group(1)
                    try:
                        dd['DataRaw'] = product_json_str
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
            for sz in response.xpath('//div[@class="product-info__variant-picker"]//fieldset[@data-option-name="size"]//div[@data-option-selector]/input/@value').getall():
                sizelist.append(sz)
            dd["SizeList"] = sizelist
            lensz = len(sizelist)
            if lensz == 0:
                lensz = 1
            dd['SizeNum'] = lensz
            if not dd['PriceText']:
                price_text = response.xpath('//div[@class="product-info__price"]//sale-price/span[@class="money"]/text()').get()
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None

            # 提取面料信息
            # fabric_info = response.xpath('//span[@class="description"]/p[strong[contains(text(), "Fabric Composition:")]]/following-sibling::p[1]/text()').get()
            # dd['Material'] = fabric_info.strip() if fabric_info else None
            # desc_nd = response.xpath('//div[@class="product__description rte quick-add-hidden"]/text()').get()
            # dd['Description'] = desc_nd.strip() if desc_nd else None
            # print("-----------parse_detail--------", dd)
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            yield dd

    @classmethod
    def export(cls):
        print("export({})".format(cls.name))