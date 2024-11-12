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
            # print("---------parse_list-------", nd.extract())
            dd = BaseProductItem()
            img = nd.xpath('//img[@class="motion-reduce"]/@src').get()
            dd['Thumbnail'] = self.get_site_url(img)
            dd['Url'] = self.get_site_url(nd.xpath('//a[@class="full-unstyled-link"]/@href').get())
            dd['Title'] = nd.xpath('//span[@class="card-information__text h5"]/text()').extract()[0].strip()
            dd['Color'] = nd.xpath('//span[@class="card-information__text card-information__colour"]/text()').extract()[0].strip()
            dd['OldPriceText'] = nd.xpath('//span[@class="price-item price-item--regular"]/text()').extract()[0].strip()
            dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText'])
            dd['PriceText'] = nd.xpath('//span[@class="price-item price-item--sale price-item--last"]/text()').get().strip()
            dd['FinalPrice'] = self.get_price_by_text(dd['PriceText'])
            self.logger.info(f"-----parse_list--dd----url={dd['Url']}-----", dd)
            print("----------base--info-------", img, dd['Title'], dd['Url'])
            yield dd
            # yield Request(dd['url'], self.parse_detail, meta=dict(dd=dd))
            
        # if response.status == 200 and len(items_nodes) == 15:
        #     nextPage = page+1
        #     nextUrl = response.url.replace(f"page={page}", f"page={nextPage}")
        #     yield Request(nextUrl, self.parse_details, meta=dict(page=nextPage))


    def parse_detail(self, response: TextResponse):
        # meta = response.meta
        # item = meta['dd']

        # item["reviews_num"] = int(reviews_num)
        # item["url"] = url
        # item["title"] = title
        # item["variants_num"] = len(color_eles)
        # item["quantity"] = quantity
        # item["detail"] = detail
        # yield item
        pass
