from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage


class OchsnersportSpider(BaseSpider):

    name = "ochsnersport"
    base_url = "https://www.ochsnersport.ch"
    allowed_domains = ["www.ochsnersport.ch"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        # 取消 URL 长度限制
        'URLLENGTH_LIMIT': None,
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Code', 'Title',  'Color', 'OldPrice', 'FinalPrice', 'Discount', 'TotalInventoryQuantity', 'SizeNum', 'SizeList', 'Tags', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'ochsnersport.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': "women shoes", 'name':'Damen', 'url': 'https://www.ochsnersport.ch/de/shop/damen-schuhe-00015643-c.html'},
        {'index': 2, 'title': 'Men Shoes', 'name':'Herren', 'url': 'https://www.ochsnersport.ch/de/shop/herren-schuhe-00015643-c.html'},
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        requrl = "https://www.ochsnersport.ch/de/shop/api/v2/search"
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex={pageindex}--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']
        hdr = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json; charset=UTF-8',
            'referer': "{}?page={}".format(gp['url'], pageindex),
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        postdata = ""
        if groupIndex == 1:
            postdata = r'{"categoryCode":"00015643","currentNavigation":{"code":"00015643"},"facets":[{"code":"gender","name":"Geschlecht","values":[{"code":"FEMALE","name":"Damen","count":1447,"selected":true}]},{"code":"navigation","name":"Kategorie","values":[{"code":"/categories/00014007/00015643","count":1447,"name":"Schuhe","selected":true,"index":true,"hideInNavigation":false}]}],"pagination":{"count":31,"options":[24,48,96],"page":'+ str(pageindex) +',"selectedOption":48,"totalCount":1447},"sorts":{"options":[{"code":"null:desc","name":"Beliebteste"},{"code":"averageRating:desc","name":"Bestbewerteste"},{"code":"onlineDate:desc","name":"Neuste"},{"code":"priceValue:asc","name":"Preis aufsteigend"},{"code":"priceValue:desc","name":"Preis absteigend"}],"selectedOption":"null:desc"},"text":""}'
        if groupIndex == 2:
            postdata = r'{"categoryCode":"00015643","currentNavigation":{"code":"00015643"},"facets":[{"code":"gender","name":"Geschlecht","values":[{"code":"MALE","name":"Herren","count":1769,"selected":true}]},{"code":"navigation","name":"Kategorie","values":[{"code":"/categories/00014007/00015643","count":1769,"name":"Schuhe","selected":true,"index":true,"hideInNavigation":false}]}],"pagination":{"count":37,"options":[24,48,96],"page":' + str(pageindex) + ',"selectedOption":48,"totalCount":1769},"sorts":{"options":[{"code":"null:desc","name":"Beliebteste"},{"code":"averageRating:desc","name":"Bestbewerteste"},{"code":"onlineDate:desc","name":"Neuste"},{"code":"priceValue:asc","name":"Preis aufsteigend"},{"code":"priceValue:desc","name":"Preis absteigend"}],"selectedOption":"null:desc"},"text":""}'
        if postdata == "":
            raise Exception("postdata is empty")
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        return Request(requrl, callback=self.parse_list, method='POST', meta=meta, headers=hdr, body=postdata)

    def start_requests(self):
        self.page_size = 48
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def check_next_page(self, page_index, group_index):
        if group_index == 1:
            return page_index < 31
        if group_index == 2:
            return page_index < 37
        return False

    def parse_list(self, response: TextResponse):
        meta = response.meta
        gp: dict = meta['gp']
        page = meta['page']
        groupName = gp.get('title')
        self.lg.debug(f"-------parse_list--group({groupName})--page={page}----requrl({response.url})---")
        has_next_page = False
        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
            dd_list = prods
            total_page = dl['TotalPage']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, gp.get('index'))
        else:
            result = response.json()
            total_count = result['pagination']['totalCount']
            page_index = result['pagination']['page']
            total_page = result['pagination']['count']
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, gp.get('index'))
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            hits = result['results']
            if hits is None or len(hits) == 0:
                # raise ValueError("models is empty")
                return
            prods = []
            dd_list = []
            for hit in hits:
                d = hit.get('product')
                if d is None:
                    continue
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                imgs = d.get('images')
                if len(imgs) > 0:
                    imgtxt = imgs[0].get('altText')
                    imgkey = imgtxt.lower().replace(' ', '-')
                    assetId = imgs[0].get('assetId')
                    # https://ochsnersport.scene7.com/asset/ochsnersport/product/tile/preset/v3-product-tile/w364/fit/fit-1/nitro-venture-pro-tls-herren-snowboardschuh--2367095_P.jpg
                    dd['Thumbnail'] = "https://ochsnersport.scene7.com/asset/ochsnersport/product/tile/preset/v3-product-tile/w364/fit/fit-1/{}--{}.jpg".format(imgkey, assetId)
                    dd['image_urls'] = [dd['Thumbnail']]
                # dd['Code'] = d.get('articleCode')
                dd['Code'] = d.get('code')
                bd = d.get('brand')
                if bd is not None:
                    dd['Brand'] = bd.get('name')
                dd['Color'] = d.get('color').get('name')
                dd['Title'] = d.get('name')
                tags = []
                for lb in d.get('labels', []):
                    tags.append(lb.get('label'))
                dd['Tags'] = tags
                if 'price' in d:
                    if 'selling' in d.get('price'):
                        dd['PriceText'] = d.get('price').get('selling').get('formattedValue')
                        dd['FinalPrice'] = d.get('price').get('selling').get('value')
                    if 'cross' in d.get('price'):
                        dd['OldPriceText'] = d.get('price').get('cross').get('formattedValue')
                        dd['OldPrice'] = d.get('price').get('cross').get('value')
                    if 'OldPrice' in dd:
                        dd['Discount'] = round((dd['OldPrice'] - dd['FinalPrice']) / dd['OldPrice'] * 100)
                    else:
                        dd['OldPrice'] = dd['FinalPrice']
                        dd['Discount'] = 0
                dd['Url'] = self.get_site_url(d.get('url'))
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
                dd_list.append(dd)
            dl['ProductList'] = prods
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.setDataRaw(response.text)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in dd_list:
            # yield prod
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            newrequrl = "https://www.ochsnersport.ch/de/shop/api/v2/products/{}?forceDb=true&updateExternalStocks=true&fields=".format(dd['Code'])
            yield Request(newrequrl, self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        if has_next_page:
            self.lg.debug(f"-----parse_list--goto({gp.get('title')})--next_page({dl['PageIndex']+1})--")
            yield self.request_list_by_group(gp, page+1)

    def parse_detail(self, response: TextResponse):
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:            
            result = response.json()
            color = result.get('color').get('name')
            total_qty = 0
            sizelist = []
            for col in result.get('colorVariants', []):
                if dd['Code'] == col.get('code') and color == col.get('color').get('name'):
                    for szvar in col.get('sizeVariants', []):
                        total_qty += szvar.get('stock').get('available')
                        for skuu in szvar.get('systems'):
                            sizeok = skuu.get('defaultSizingSystem')
                            if sizeok:
                                sizelist.append(skuu.get('value'))
            dd['TotalInventoryQuantity'] = total_qty
            dd["SizeList"] = sizelist
            lensz = len(sizelist)
            if lensz == 0:
                lensz = 1
            dd['SizeNum'] = lensz
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            dd['DataRaw'] = response.text
            yield dd

