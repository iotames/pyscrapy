from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
# from service import Config
# import os
import re
import json


class VarleySpider(BaseSpider):
    name = "varley"
    base_url = "https://www.varley.com"
    allowed_domains = ["www.varley.com"]

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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'PublishedAt', 'Title', 
                                'PriceText', 'FinalPrice', 'TotalInventoryQuantity', 'SizeNum', 'SizeList', 'Tags', 'Image', 'Description', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'varley.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': 'All', 'name':'all', 'url': 'https://www.varley.com/collections/all'},
    ]
    # start_urls = []

    def get_prods_by_text(self, body: str) ->list:
        # 使用正则表达式提取 JSON 数据
        match = re.search(r'window\.__remixContext\s*=\s*({.*?});', body, re.DOTALL)
        if match:
            json_data = match.group(1)
            # 将 JSON 字符串转换为 Python 字典
            data = json.loads(json_data)
            prods = data.get("state").get("loaderData").get("routes/($lang).collections.$handle").get("products")
            return prods
        else:
            raise ValueError("JSON data not found in the HTML")

    def request_list_by_group(self, gp: dict, pageindex: int):
        if pageindex > 1:
            raise ValueError("page index must be 1")
        group_name = gp.get('name')
        requrl = "{}/collections/{}".format(self.base_url, group_name)
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            # 'referer': gp.get('url'),
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        # htmlfile = os.path.join(Config.get_instance().get_root_path(), 'runtime', 'varley.all.html')
        # if os.path.exists(htmlfile):
        #     with open(htmlfile, "r", encoding="utf-8") as file:
        #         body=file.read()
        #         prods = self.get_prods_by_text(body)
        #         print(prods)
        #     return
        self.page_size = 700
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def check_next_page(self, page_index, total_page):
        return False
        # return page_index < total_page

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
            total_page = dl['TotalPage']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_page)
        else:
            prodraws = self.get_prods_by_text(response.text)
            prodslen = len(prodraws)
            total_count = prodslen
            page_index = page
            total_page = 1
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_page)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            
            prods = []
            for ddd in prodraws:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                dd['PriceText'] = ddd.get('priceV2').get('amount') + " " + ddd.get('priceV2').get('currencyCode')
                code = ddd.get('selectedVariantId')
                dd['Code'] = code.replace("gid://shopify/ProductVariant/", "")
                dd['FinalPrice'] = float(ddd.get('priceV2').get("amount"))
                d = ddd.get('product')
                for optv in d.get('options', []):
                    if optv.get('name') == 'Size':
                        dd['SizeList'] = optv.get('values', [])
                        dd['SizeNum'] = len(dd['SizeList'])
                variants_list = d.get('variants')
                if variants_list is not None:
                    totalqty = 0
                    variants = []
                    for s in variants_list.get('nodes', []):
                        totalqty += s['quantityAvailable']
                        selectOpts = s.get('selectedOptions', [])
                        sz = ""
                        for sopt in selectOpts:
                            if sopt['name'] == 'Size':
                                sz = sopt['value']
                        variants.append({'Code': s['sku'], 'Size': sz, 'Title': s.get("title"), 'Quantity': s['quantityAvailable']})
                    dd['TotalInventoryQuantity'] = totalqty
                    dd['Variants'] = variants
                dd['PublishedAt'] = d.get('publishedAt')
                dd['UrlKey'] = d.get('handle')
                dd['Tags'] = d.get("tags", [])
                dd['Title'] = d.get('title')
                # dd['Category'] = d.get('type')
                if dd['UrlKey'] is None:
                    continue
                # https://www.varley.com/products/sandy-zip-through-knit-gilet?variant=43897944572077
                dd['Url'] = "{}/products/{}?variant={}".format(self.base_url, dd['UrlKey'], dd['Code'])
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            dl['ProductList'] = prods
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.setDataRaw(str(prodraws))
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            # yield dd
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            requrl = "{}/api/products/{}".format(self.base_url, dd['UrlKey'])
            hdr = {
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'referer': gp.get('url'),
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            }
            yield Request(requrl, self.parse_detail, headers=hdr, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
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
            dd['DataRaw'] = response.text
            jsdt = response.json()
            data = jsdt['product']
            dd['Brand'] = data.get("vendor")
            dd['Title'] = data['title']
            dd['PublishedAt'] = data['publishedAt']
            dd['Description'] = data['description']
            dd['Tags'] = data['tags']
            dd['Image'] = data['featuredImage']['url']
            dd['Thumbnail'] = dd['Image'] + "&width=200"
            dd['image_urls'] = [dd['Thumbnail']]
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            yield dd