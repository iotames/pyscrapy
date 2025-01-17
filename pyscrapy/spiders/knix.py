from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
from urllib.parse import quote


class KnixSpider(BaseSpider):

    name = "knix"
    base_url = "https://knix.com"
    allowed_domains = ["knix.com"]

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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Code', 'PublishedAt', 'Title', 'Color', 'SubTitle',
                               'OldPrice', 'FinalPrice', 'TotalInventoryQuantity', 'TotalReviews', 'ReviewRating',   'SizeNum', 'SizeList','Tags', 
                               'Material', 'Description', 'Image', 'Url'
        ],
        'FEED_EXPORT_FIELDS_DICT': {"SubTitle": "Absorbency"}
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'knix.xlsx',
        # 'FEED_FORMAT': 'xlsx'
        }

    start_urls_group = [
        {'index': 1, 'title': 'Wireless Bras', 'name':'bras', 'url': 'https://knix.com/collections/bras'}, # 39
        {'index': 2, 'title': 'Active', 'name':'activewear', 'url': 'https://knix.com/collections/activewear'}, # 33
        {'index': 3, 'title': 'Swim', 'name':'swimwear', 'url': 'https://knix.com/collections/swimwear'}, # 20
        {'index': 4, 'title': 'All Underwear', 'name':'all-underwear', 'url': 'https://knix.com/collections/all-underwear'}, # 71
        {'index': 5, 'title': 'Shapewear', 'name': 'shapewear', 'url': 'https://knix.com/collections/shapewear'}, # 23
        {'index': 6, 'title': 'Sleepwear', 'name': 'sleepwear', 'url': 'https://knix.com/collections/sleepwear'}, # 15
        {'index': 7, 'title': 'Loungewear', 'name': 'loungewear', 'url': 'https://knix.com/collections/loungewear'}, # 7
        {'index': 8, 'title': 'Shop All Teen', 'name': 'shop-all-teen', 'url': 'https://knix.com/collections/shop-all-teen'} # 55
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        requrl = "https://knix.com/collections/{}?page={}&_data={}".format(group_name, pageindex, quote("routes/collections+/$handle"))
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        referer = gp.get('url')
        if pageindex > 1:
            referer = "{}?page={}".format(gp.get('url'), pageindex-1)
        hdr = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 60
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def check_next_page(self, page_index, total_page):
        return page_index < total_page

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
            result = response.json()
            total_count = result.get('pagination', {}).get('totalResults', 0)
            page_index = result.get('pagination', {}).get('currentPage', 0)
            total_page = result.get('pagination', {}).get('totalPages', 0)
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_page)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            dd_list = result.get('products', [])
            if len(dd_list) == 0:
                raise ValueError("products is empty")
            prods = []
            for d in dd_list:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                d_options = d.get('options', [])
                for d_option in d_options:
                    if d_option['name'] == 'Size':
                        dd['SizeList'] = d_option.get('values', [])
                        dd['SizeNum'] = len(dd['SizeList'])                    
                d_nodes = d.get('variants', {}).get('nodes', [])
                variants = []
                for d_node in d_nodes:
                    variants.append({'Code': d_node['sku'], 'Title': d_node['title']})
                dd['Variants'] = variants
                dd['UrlKey'] = d.get('handle')
                if dd['UrlKey'] is None:
                    continue
                dd['Url'] = "https://knix.com/products/{}".format(d.get('handle'))
                dd['TotalInventoryQuantity'] = d.get('totalInventory', 0)
                dd['Title'] = d.get('title')
                dd['PublishedAt'] = d.get('publishedAt')
                okendoReviewCountObj = d.get('okendoReviewCount')
                okendoRatingValueObj = d.get('okendoRatingValue')
                dd['TotalReviews'] = int(okendoReviewCountObj.get('value', 0)) if okendoReviewCountObj is not None else 0
                dd['ReviewRating'] = float(okendoRatingValueObj.get('value', 0)) if okendoRatingValueObj is not None else 0
                absorbencyLevel = ""
                if 'absorbencyLevel' in d:
                    absobj = d.get('absorbencyLevel')
                    absorbencyLevel = absobj.get('value', "") if absobj is not None else ""
                tags = d.get('tags', [])
                if absorbencyLevel != "":
                    tags.append(absorbencyLevel)
                    dd['SubTitle'] = absorbencyLevel
                compareAtPriceStr = d.get('compareAtPriceRange', {}).get('minVariantPrice', {}).get('amount', "0.0")
                priceStr = d.get('priceRange', {}).get('minVariantPrice', {}).get('amount', "0.0")
                dd['FinalPrice'] = float(priceStr)
                dd['OldPrice'] = float(compareAtPriceStr)
                if dd['OldPrice'] == 0:
                    dd['OldPrice'] = dd['FinalPrice']
                dd['Color'] = d.get('custom', {}).get('color', "")
                
                img = d.get('featuredImage', {}).get('url', "")
                dd['Image'] = img
                dd['Thumbnail'] = img + "&width=600&height=778&crop=center"
                dd['image_urls'] = [dd['Thumbnail']]
                productFabricationCareObj = d.get('productFabricationCare')
                productFabricationCare = productFabricationCareObj.get('value', "") if productFabricationCareObj is not None else ""
                dd['Description'] = productFabricationCare
                materials = get_material(productFabricationCare)
                dd['Material'] = ",".join(materials)
                dd['Category'] = d.get('productType')
                dd['Tags'] = tags
                dd['Code'] = d.get('id')
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            
            dl['ProductList'] = prods
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.setDataRaw(response.text)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for prod in prods:
            yield prod
            # prod['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            # yield Request(prod['Url'], self.parse_detail, meta=dict(dd=prod, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        if has_next_page:
            self.lg.debug(f"-----parse_list--goto({gp.get('title')})--next_page({dl['PageIndex']+1})--")
            yield self.request_list_by_group(gp, page+1)

    # def parse_detail(self, response: TextResponse):
    #     meta = response.meta
    #     dd = meta['dd']
    #     if 'SkipRequest' in dd:
    #         # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
    #         yield dd
    #     else:
    #         jsonstr = self.get_text_by_path(response, '//script[@type="application/ld+json"]/text()')
    #         if jsonstr is not None:
    #             dd['DataRaw'] = jsonstr
    #         # print("-----------parse_detail--------", dd)
    #         # self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}--desc({dd['Description']})--")
    #         yield dd
