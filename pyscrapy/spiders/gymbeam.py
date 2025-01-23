from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
from urllib.parse import quote
import os
from utils.os import save_file


class GymbeamSpider(BaseSpider):

    name = "gymbeam"
    base_url = "https://gymbeam.com"
    allowed_domains = ["gymbeam.com"]

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
        # 'FEED_URI': 'gymbeam.xlsx',
        # 'FEED_FORMAT': 'xlsx'
        }
# https://gymbeam.com/clothing?p=6
    start_urls_group = [
        {'index': 1, 'title': 'Sportswear', 'name':'clothing', 'url': 'https://gymbeam.com/clothing'}, # 39
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        groupIndex = gp.get('index')
        requrl = "https://gymbeam.com/{}?p={}&is_scroll=1".format(group_name, pageindex)
        # if pageindex == 1:
        #     requrl = gp.get('url')
        referer_page = pageindex - 2
        referer = gp.get('url')
        if referer_page > 1:
            referer = "{}?p={}".format(gp.get('url'), referer_page)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 36
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def check_next_page(self, page_index, total_count):
        return page_index * self.page_size < total_count

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
            total_count = dl['TotalCount']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_count)
        else:
            # //li[@class="item product product-item"]
            filename = "runtime/{}.json".format(self.name)
            result = response.json()
            categoryProducts = result.get('categoryProducts')
            if categoryProducts is None:
                raise ValueError("categoryProducts is empty")
            save_file(filename, categoryProducts)
            total_count = result.get('productsAmount', {}).get('total', 0)
            page_index = page
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}

            dd_list = ""
            if len(dd_list) == 0:
                raise ValueError("products is empty")
            prods = []
            for d in dd_list:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                img = ""
                dd['Image'] = img
                dd['Thumbnail'] = img + "&width=600&height=778&crop=center"
                dd['image_urls'] = [dd['Thumbnail']]
                productFabricationCare = ""
                dd['Description'] = productFabricationCare
                materials = get_material(productFabricationCare)
                dd['Material'] = materials
      
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
