from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage


class XexymixSpider(BaseSpider):

    name = "xexymix"
    base_url = "https://www.xexymix.com"
    allowed_domains = ["www.xexymix.com", "cdn1-aka.makeshop.co.kr"]

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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'ParentGroup','GroupName', 'Code', 'Spu', 'Title', 'SubTitle', 
                               'PriceText', 'OldPrice', 'FinalPrice', 'Url'
        ],
        'FEED_EXPORT_FIELDS_DICT': {"ParentGroup": "大类", "GroupName": "小类"}
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'xexymix.xlsx',
        # 'FEED_FORMAT': 'xlsx'
        }

    # start_urls_group = [
    #     # {'index': 1, 'title': 'WOMENS', 'name':'033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&type=X'}, # 2486
    #     # {'index': 2, 'title': 'MENS', 'name':'011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&type=X'}, # 485
    #     # {'index': 3, 'title': 'GOLF', 'name':'004', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=004&type=Y'}, # 442
    #     # {'index': 4, 'title': 'SHOES & ACC', 'name':'035', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=035&type=X'}, # 289
    #     # {'index': 5, 'title': 'KIDS', 'name':'001', 'url': 'https://www.xexymix.com/m/product_list.html?xcode=001&type=X'}, # 238
    # ]

    start_urls_group = [
    {'index': 1, 'title': '우먼즈-비즈니스웨어', 'name': '022', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=022&mcode=011&scode=001&type=Y'},  # 우먼즈-비즈니스웨어
    {'index': 2, 'title': '우먼즈-레깅스', 'name': '034', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=034&mcode=001&type=Y'},  # 우먼즈-레깅스
    {'index': 3, 'title': '우먼즈-조거팬츠', 'name': '034', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=034&mcode=002&type=Y'},  # 우먼즈-조거팬츠
    {'index': 4, 'title': '우먼즈-상의', 'name': '033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&mcode=001&type=X'},  # 우먼즈-상의
    {'index': 5, 'title': '우먼즈-패드탑', 'name': '033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&mcode=002&type=X'},  # 우먼즈-패드탑
    {'index': 6, 'title': '우먼즈-아우터', 'name': '033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&mcode=003&type=X'},  # 우먼즈-아우터
    {'index': 7, 'title': '우먼즈-하의', 'name': '033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&mcode=004&type=X'},  # 우먼즈-하의
    {'index': 8, 'title': '우먼즈-이너웨어', 'name': '033', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=033&mcode=005&type=X'},  # 우먼즈-이너웨어
    {'index': 9, 'title': '우먼즈-블랙라벨', 'name': '024', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=024&type=Y'},  # 우먼즈-블랙라벨
    {'index': 10, 'title': '우먼즈-스윔웨어', 'name': '021', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=021&mcode=011&type=Y'},  # 우먼즈-스윔웨어
    {'index': 11, 'title': '우먼즈-러닝라인', 'name': '007', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=007&mcode=001&type=Y'},  # 우먼즈-러닝라인

    {'index': 12, 'title': '맨즈-비즈니스웨어', 'name': '022', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=022&mcode=011&scode=002&type=Y'},  # 맨즈-비즈니스웨어
    {'index': 13, 'title': '맨즈-신상', 'name': '027', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=027&mcode=004&type=Y'},  # 맨즈-신상
    {'index': 14, 'title': '맨즈-상의', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=010&type=X'},  # 맨즈-상의
    {'index': 15, 'title': '맨즈-아우터', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=011&type=X'},  # 맨즈-아우터
    {'index': 16, 'title': '맨즈-하의', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=012&type=X'},  # 맨즈-하의
    {'index': 17, 'title': '맨즈-슬랙스', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=012&scode=001&type=X'},  # 맨즈-슬랙스
    {'index': 18, 'title': '맨즈-조거팬츠', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=012&scode=002&type=X'},  # 맨즈-조거팬츠
    {'index': 19, 'title': '맨즈-탄성팬츠', 'name': '022', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=022&mcode=006&type=Y'},  # 맨즈-탄성팬츠
    {'index': 20, 'title': '맨즈-이너웨어', 'name': '011', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=011&mcode=013&type=X'},  # 맨즈-이너웨어
    {'index': 21, 'title': '맨즈-블랙라벨', 'name': '024', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=024&mcode=001&type=Y'},  # 맨즈-블랙라벨
    {'index': 22, 'title': '맨즈-스윔웨어', 'name': '021', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=021&type=N&mcode=004'},  # 맨즈-스윔웨어
    {'index': 23, 'title': '맨즈-짐웨어', 'name': '006', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=006&mcode=005&type=Y'},  # 맨즈-짐웨어
    {'index': 24, 'title': '맨즈-러닝라인', 'name': '007', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=007&mcode=002&type=Y'},  # 맨즈-러닝라인

    {'index': 25, 'title': '골프-우먼즈', 'name': '004', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=004&mcode=001&type=Y'},  # 골프-우먼즈
    {'index': 26, 'title': '골프-맨즈', 'name': '004', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=004&mcode=002&type=Y'},  # 골프-맨즈
    {'index': 27, 'title': '골프-용품', 'name': '004', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=004&mcode=003&type=Y'},  # 골프-용품

    {'index': 28, 'title': '키즈-상의', 'name': '001', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=001&mcode=007&type=X'},  # 키즈-상의
    {'index': 29, 'title': '키즈-아우터', 'name': '001', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=001&mcode=008&type=X'},  # 키즈-아우터
    {'index': 30, 'title': '키즈-하의', 'name': '001', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=001&mcode=009&type=X'},  # 키즈-하의
    {'index': 31, 'title': '키즈-슈즈&용품', 'name': '001', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=001&mcode=010&type=X'},  # 키즈-슈즈&용품
    {'index': 32, 'title': '키즈-스윔웨어', 'name': '021', 'url': 'https://www.xexymix.com/shop/shopbrand.html?xcode=021&mcode=008&type=Y'},  # 키즈-스윔웨어
]


    # start_urls = []

    def get_requrl_by_gp(self, gp: dict, pageindex: int):
        if pageindex > 1:
            return "{}&sort=&page={}".format(gp.get('url'), pageindex)
        return gp.get('url')

    def request_list_by_group(self, gp: dict, pageindex: int):
        # group_name = gp.get('name')
        requrl = self.get_requrl_by_gp(gp, pageindex)
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'referer': 'https://www.xexymix.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        if pageindex > 1:
            hdr['referer'] = self.get_requrl_by_gp(gp, pageindex-1)
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 200
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
            # //div[@class="item-cont"]/dl
            nds = response.xpath('//div[@class="item-cont"]/dl')
            if len(nds) == 0:
                raise ValueError("parse_list--nds is empty")
            total_str = self.get_text_by_path(response, '//div[@class="item-sort"]/p/strong/text()')
            total_count = 0
            if total_str is not None:
                total_count = int(total_str.replace(',', ''))
            if total_count == 0:
                raise ValueError("total_count is 0")
            page_index = page
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'PageIndex': page_index, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            prods = []
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                groupSplit = groupName.split('-')
                dd['ParentGroup'] = groupSplit[0]
                dd['GroupName'] = groupSplit[1]
                dd['PageIndex'] = page_index
                purl = self.get_text_by_path(nd, 'dt/a/@href')
                if purl is None:
                    continue
                dd['Url'] = self.get_site_url(purl)
                dd['Spu'] = self.get_text_by_path(nd, './/span[@class="style-code"]/text()')
                dd['Code'] = self.get_text_by_path(nd, 'dt/a/img/@data-product_uid')
                img = self.get_text_by_path(nd, 'dt/a/img/@data-frz-src')
                if img is not None:
                    img = "https:" + img
                    dd['Thumbnail'] = img
                    dd['image_urls'] = [img]
                dd['Title'] = self.get_text_by_path(nd, './/li[@class="prd-name"]/text()')
                salePriceText = self.get_text_by_path(nd, './/div[@class="priceBox"]/li[1]/text()') # 69,000
                oldPriceText = self.get_text_by_path(nd, './/li[@class="prd-price"]/strike[@class="o_prd"]/text()') # 69,000
                dd['PriceText'] = salePriceText
                dd['OldPriceText'] = oldPriceText
                dd['FinalPrice'] = float(salePriceText.replace(',', ''))
                dd['OldPrice'] = float(oldPriceText.replace(',', '')) if oldPriceText is not None else dd['FinalPrice']
                dd['SubTitle'] = self.get_text_by_path(nd, './/li[@class="prd-name-sub"]/text()')
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            dl['ProductList'] = prods
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            # ur.setDataRaw(response.text)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for prod in prods:
            if 'image_urls' not in prod:
                prod['image_urls'] = [prod['Thumbnail']]
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
