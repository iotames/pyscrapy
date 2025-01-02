from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from service import Config
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from urllib.parse import quote
import os


class EllosSpider(BaseSpider):
    name = "ellos"
    base_url = "https://www.ellos.se"
    allowed_domains = ["www.ellos.se"]

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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Spu', 'Code', 'Title', 'Color',
                                'PriceText', 'FinalPrice', 'OldPrice', 'Discount', 'ReviewRating', 'SizeNum', 'SizeList', 'Tags', 'Image', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'ellos.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': "Women's Clothing & Shoes", 'name':'/campaign/party-ladies/dam', 'url': 'https://www.ellos.se/campaign/party-ladies/dam'}, # 392
        {'index': 2, 'title': "Sports & outdoors", 'name':'/dam/sport-outdoor', 'url': 'https://www.ellos.se/dam/sport-outdoor'}, # 4201
        {'index': 3, 'title': "Men Clothes", 'name':'/herr/mode', 'url': 'https://www.ellos.se/herr/mode'}, # 3288
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        # https://www.ellos.se%2Fdam%2Fsport-outdoor
        requrl = "{}/api/es/articles/?path={}&page={}".format(self.base_url, quote(group_name), pageindex)
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept-language': 'sv-SE',
            'referer': gp.get('url'),
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-channel': 'ellos_SE',
            # 'x-correlation-id': 'www.ellos.se-1735800047370-1047'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 58
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def check_next_page(self, page_index, total_page):
        return page_index < total_page

    def parse_list(self, response: TextResponse):
        meta = response.meta
        gp: dict = meta['gp']
        page = meta['page']
        groupName = gp.get('title')
        # self.lg.debug(f"-------parse_list--group({groupName})--page={page}----requrl({response.url})---")
        htmlfile = os.path.join(Config.get_instance().get_root_path(), 'runtime', '{}.list.html'.format(self.name))
        if not os.path.exists(htmlfile):
            with open(htmlfile, "w", encoding="utf-8") as file:
                file.write(response.text)

        has_next_page = False

        if 'dl' in meta:
            # self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
            total_page = dl['TotalPage']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_page)
        else:
            datajson = response.json()
            articles = datajson.get("articles", [])
            prodslen = len(articles)
            if prodslen == 0:
                raise ValueError("parse_list--no product")
            total_count = datajson.get("count").get("total")
            page_index = datajson.get("pagination").get("current")
            total_page = datajson.get("pagination").get("last")
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_page)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            
            prods = []
            for d in articles:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                dd['Color'] = d.get("color", '')
                dd['Tags'] = d.get("categories", [])
                dd['FinalPrice'] = float(d['currentPrice'])
                dd['Discount'] = d['discountAmount']
                if dd['Discount'] > 0:
                    dd['OldPrice'] = float(d['originalPrice'])
                else:
                    dd['OldPrice'] = dd['FinalPrice']
                dd['Spu'] = d.get('id', '')
                dd['Code'] = d['sku']
                imgobj = d.get("imageAlternative", None)
                if imgobj is not None:
                    dd['Thumbnail'] = imgobj.get("card").replace("mw={size}", "mw=300")
                    dd['Image'] = dd['Thumbnail'].replace("mw=300", "")
                    # dd['image_urls'] = [dd['Thumbnail']]
                dd['Title'] = d['name']
                dd['PriceText'] = "{} SEK".format(dd['FinalPrice'])
                dd['ReviewRating'] = float(d['rating']) if d.get('rating', None) is not None else 0
                dd['ColorNum'] = len(d.get('relatedArticles', []))
                sub_brand_seo = d.get('subBrandSeo', None)
                name_seo = d.get('nameSeo', None)
                if sub_brand_seo is None or name_seo is None:
                    continue
                dd['Url'] = "{}/{}/{}/{}".format(self.base_url, sub_brand_seo, name_seo, d['id'])
                size_list = []
                for skd in d.get('skusData', []):
                    size_list.append(skd.get('size', None))
                dd['SizeList'] = size_list
                lensize = len(dd['SizeList'])
                dd['SizeNum'] = lensize if lensize > 0 else 0
                if len(dd['Tags']) > 0:
                 dd['Category'] = dd['Tags'][len(dd['Tags']) - 1]
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
        for dd in prods:
            yield dd
            # dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            # # requrl = "{}/api/products/{}".format(self.base_url, dd['UrlKey'])
            # requrl = dd['Url']
            # hdr = {
            #     'accept': '*/*',
            #     'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            #     'referer': gp.get('url'),
            #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            # }
            # yield Request(requrl, self.parse_detail, headers=hdr, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        if has_next_page:
            # self.lg.debug(f"-----parse_list--goto({gp.get('title')})--next_page({dl['PageIndex']+1})--")
            yield self.request_list_by_group(gp, page+1)
