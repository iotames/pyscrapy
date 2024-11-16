from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
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
        'FEED_URI': 'aybl.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'Category', 'Title',  'Color', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url']
    }


    def start_requests(self):
        for requrl in self.start_urls:
            print('------start_requests----', requrl)
            # mustin = ['step', 'page', 'group', 'FromKey']
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1, step=1, group=1, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        print(f"------------page={page}----", response.url)
        self.logger.debug(f"---------parse_list--page={page}---")

        if 'dl' in meta:
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            nds = response.xpath('//ul[@id="product-grid"]/li')
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['image_urls'] = [dd['Thumbnail']]
                prods.append(dd)
            nextPageUrl = ""
            next_page = response.xpath('//a[@aria-label="Next page"]/@href').get()
            if next_page:
                nextPageUrl = self.get_site_url(next_page)
            dl = {'ProductList': prods, 'NextPageUrl': nextPageUrl}
            ur = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.save(meta['StartAt'])
            
        
        for dd in prods:
            # yield dd
            yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        
        if dl['NextPageUrl'] != "":
            print(f"------------next_page-{dl['NextPageUrl']}---")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=dict(page=page+1, step=meta['step'], group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_detail(self, response: TextResponse):
        pass