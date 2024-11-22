from scrapy.http import TextResponse
# from scrapy_splash import SplashRequest
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
import json


class NoseridersurfSpider(BaseSpider):
    name = "elcorteingles"
    base_url = "https://www.elcorteingles.es"
    allowed_domains = ["www.elcorteingles.es", '127.0.0.1']

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
        # 'FEED_URI': 'elcorteingles.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        # https://www.elcorteingles.es/adidas-samba/adidas/deportes/calzado/3/, https://www.elcorteingles.es/deportes/running/zapatillas/
        # https://www.elcorteingles.es/deportes/running/zapatillas/2/, https://www.elcorteingles.es/adidas-samba/adidas/deportes/calzado/
        {'index': 1, 'title': 'Adidas Samba · Deportes · Calzado', 'url': 'https://www.elcorteingles.es/api/firefly/vuestore/products_list/adidas-samba/adidas/deportes/calzado/1/?showDimensions=none'},
        {'index': 2, 'title': 'Zapatillas running', 'url': 'https://www.elcorteingles.es/api/firefly/vuestore/products_list/deportes/running/zapatillas/1/?showDimensions=none'},
    ]
    
    # start_urls = []
    
    def start_requests(self):
        self.page_size = 11
        for gp in self.start_urls_group:
            requrl = gp['url']
            groupName = gp['title']
            groupIndex = gp['index']
            print('------start_requests----', groupIndex, groupName, requrl)
            hdrs = {"Accept": "application/json, text/plain, */*"}
            meta = dict(page=1, step=1, group=groupIndex, GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
            yield Request(requrl, callback=self.parse_list, headers=hdrs, meta=meta)
            # yield SplashRequest(requrl, callback=self.parse_list, headers=hdrs, meta=meta)            

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
            result = response.json()
            if not result['success']:
                return
            total_page = result['pagination']['_total']
            page_index = result['pagination']['_current']
            total_count = result['pagination']['count']
            page_size = result['pagination']['itemsPerPage']
            products = result['data']['products']
            for pdd in products:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['Title'] = pdd['title']
                dd['PageIndex'] = page_index
                produrl = pdd['_uri']
                dd['Url'] = self.get_site_url(produrl)
                dd['Code'] = pdd['id']
                dd['Brand'] = pdd['brand']['name']
                dd['Color'] = pdd['image']['color']
                dd['Image'] = pdd['image']['sources']['big']
                dd['Thumbnail'] = pdd['image']['sources']['small']
                dd['Tags'] = [pdd['group_by']]
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            nextPageUrl = ""
            if page_index < total_page:
                nextPageUrl = response.request.url.replace(f"/{page_index}/?showDimensions=none", f"/{page_index+1}/?showDimensions=none")
            dl = {'PageSize': page_size, 'TotalCount': total_count, 'TotalPage': total_page, 'ProductList': prods, 'NextPageUrl': nextPageUrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.setDataRaw(response.text)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))

        if dl['NextPageUrl'] != "":
            print(f"------------next_page-{dl['NextPageUrl']}---")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, headers={"Accept": "application/json, text/plain, */*"}, meta=dict(page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_detail(self, response: TextResponse):         
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:
            script_text = response.xpath("//script[@type='application/ld+json'][contains(text(), 'priceCurrency')]/text()").get()
            pdd = json.loads(script_text.strip())
            dd['Title'] = pdd['name']
            dd['Description'] = pdd['description']
            dd['Url']=pdd['url']
            dd['Images'] = pdd['image']
            dd['PriceText'] = str(pdd['offers']['price']) + pdd['offers']['priceCurrency']
            dd['OldPrice'] = pdd['offers']['hightPrice']
            dd['FinalPrice'] = pdd['offers']['price']
            dd['Brand'] = pdd['brand']
            dd['image_urls'] = [dd['Thumbnail']]
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            yield dd


