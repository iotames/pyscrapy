from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage


class NoseridersurfSpider(BaseSpider):
    name = "noseridersurf"
    base_url = "https://noseridersurf.com"
    allowed_domains = ["noseridersurf.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'PublishedAt', 'Title', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'noseridersurf.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': 'Cropped Rash Guards', 'url': 'https://noseridersurf.com/collections/cropped-rash-guard'},
        {'index': 2, 'title': 'Retro Surf Suits', 'url': 'https://noseridersurf.com/collections/retro-surf-suits'},
        {'index': 3, 'title': 'Surf Bikinis', 'url': 'https://noseridersurf.com/collections/surf-bikinis'},
        {'index': 4, 'title': 'Bikini Tops', 'url': 'https://noseridersurf.com/collections/bikini-tops'},
        {'index': 5, 'title': 'Bikini Bottoms', 'url': 'https://noseridersurf.com/collections/bikini-bottoms'},
        {'index': 6, 'title': 'Surf Shorts', 'url': 'https://noseridersurf.com/collections/surf-shorts-women'},
        {'index': 7, 'title': 'Surf Leggings', 'url': 'https://noseridersurf.com/collections/surf-leggings'},
        {'index': 8, 'title': 'long sleeve surf suits', 'url': 'https://noseridersurf.com/collections/long-sleeve-surf-suits'},
        {'index': 9, 'title': 'Modest Swimwear', 'url': 'https://noseridersurf.com/collections/modest-swimwear'},
        {'index': 10, 'title': 'Overswim', 'url': 'https://noseridersurf.com/collections/overswim'},
        {'index': 11, 'title': 'Jumpers', 'url': 'https://noseridersurf.com/collections/jumpers'},
        {'index': 12, 'title': 'Corduroy Totes', 'url': 'https://noseridersurf.com/collections/corduroy-tote-bags'},
        {'index': 13, 'title': 'Shop Sale', 'url': 'https://noseridersurf.com/collections/sale'},
        {'index': 14, 'title': 'All', 'url': 'https://noseridersurf.com/collections/all'},
    ]
    
    # start_urls = []
    
    def start_requests(self):
        self.page_size = 11
        for gp in self.start_urls_group:
            requrl = gp['url']
            groupName = gp['title']
            groupIndex = gp['index']
            print('------start_requests----', groupIndex, groupName, requrl)
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1, step=1, group=groupIndex, GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))            

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        groupName = meta['GroupName']
        self.lg.debug(f"-------parse_list---requrl:{response.url}--page={page}--")

        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            # 1. 获取当前页所有商品
            nds = response.xpath('//ul[@id="product-grid"]/li')
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                
                url = nd.xpath('.//a[@class="product-card-title"]/@href').get()
                dd['Url'] = self.get_site_url(url)
                
                title = nd.xpath('.//a[@class="product-card-title"]/text()').get()
                dd['Title'] = title.strip() if title else None
                
                old_price_text = nd.xpath('.//span[@class="price"]/del/span/text()').get()
                dd['OldPriceText'] = old_price_text.strip() if old_price_text else None
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None
                
                price_text = nd.xpath('.//span[@class="price"]/ins/span/text()').get()
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            nextPageUrl = ""
            next_page = response.xpath('//ul[@class="page-numbers nav-links"]/li[@class="next"]/a/@href').get()
            if next_page:
                nextPageUrl = self.get_site_url(next_page)
            dl = {'ProductList': prods, 'NextPageUrl': nextPageUrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield Request(dd['Url'] + ".js", self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        
        if dl['NextPageUrl'] != "":
            print(f"------------next_page-{dl['NextPageUrl']}---")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=dict(page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_detail(self, response: TextResponse):        
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:
            dd['DataRaw'] = response.text
            data = response.json()
            dd['Title'] = data['title']
            dd['PublishedAt'] = data['published_at']
            dd['Description'] = data['description']
            dd['Tags'] = data['tags']
            dd['Image'] = self.get_site_url(data['featured_image'])
            dd['Thumbnail'] = dd['Image'] + "&width=200"
            szs = []
            for vv in data['variants']:
                szs.append(vv['title'])
            dd['SizeList'] = szs
            dd['SizeNum'] = len(szs)
            dd['FinalPrice'] = float(data['price']/100)
            if data['compare_at_price']:
                dd['OldPrice'] = float(data['compare_at_price']/100)
            else:
                dd['OldPrice'] = dd['FinalPrice']
            dd['image_urls'] = [dd['Thumbnail']]
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            yield dd


