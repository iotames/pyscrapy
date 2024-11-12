from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem

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
    }

    def start_requests(self):
        for requrl in self.start_urls:
            print('------start_requests----', requrl)
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1))

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        print(f"------------page={page}----", response.url)
        self.logger.debug(f"---------parse_list--page={page}---")
        nds = response.xpath('//ul[@id="product-grid"]/li')

        for nd in nds:
            dd = BaseProductItem()
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
            yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd))

        next_page = response.xpath('//a[@aria-label="Next page"]/@href').get()
        if next_page:
            next_page_url = self.get_site_url(next_page)
            next_page_num = page + 1
            print(f"---------------next_page-{next_page_num}-", next_page_url)
            yield Request(next_page_url, callback=self.parse_list, meta=dict(page=next_page_num))

    def parse_detail(self, response: TextResponse):
        meta = response.meta
        dd = meta['dd']
        sizelist = []
        for sz in response.xpath('//input[@name="Size"]/@value').getall():
            sizelist.append(sz)
        dd["SizeList"] = sizelist
        lensz = len(sizelist)
        if lensz == 0:
            lensz = 1
        dd['SizeNum'] = lensz
        yield dd
