from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage


class IntersportfrSpider(BaseSpider):
    name = "intersportfr"
    base_url = "https://www.intersport.fr"
    allowed_domains = ["www.intersport.fr", '127.0.0.1']

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Brand', 'Title', 'PriceText', 'OldPrice', 'FinalPrice', 'TotalReviews', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'intersportfr.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        # https://www.intersport.fr/sportswear/homme/chaussures/
        # https://www.intersport.fr/sportswear/femme/chaussures/?page=2
        {'index': 1, 'title': "Men's shoes", 'url': 'https://www.intersport.fr/sportswear/homme/chaussures/'},
        # {'index': 2, 'title': "Women's shoes", 'url': 'https://www.intersport.fr/sportswear/femme/chaussures/'},
    ]

    def start_requests(self):
        self.page_size = 40
        for gp in self.start_urls_group:
            requrl = gp['url']
            groupName = gp['title']
            groupIndex = gp['index']
            print('------start_requests----', groupIndex, groupName, requrl)
            meta = dict(browser=True, page=1, step=1, group=groupIndex, GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
            yield Request(requrl, callback=self.parse_list, meta=meta)
            # yield SplashRequest(requrl, callback=self.parse_list, headers=hdrs, meta=meta)

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        groupName = meta['GroupName']
        self.lg.debug(f"----parse_list--group({groupName})--page={page}---requrl:{response.url}--")

        if 'dl' in meta:
            dlur = meta['UrlRequest']
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}---ur.id({dlur.id})")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            nds = response.xpath('//div[@id="product__container"]/article')
            if len(nds) == 0:
                return
            totalStr = self.get_text_by_path(response, '//div[@class="section-header-page__title"]/small/text()')
            self.lg.debug(f"----------parse_list----TotalStr:({totalStr})------")
            # ----------parse_list----TotalStr:(1 882 produits)------
            total_count = int(totalStr.replace(' produits', '').replace(' ', '')) if totalStr else 0
            iii = 0
            for nd in nds:
                prodnd = nd.xpath('div[@class="product-box"]')
                if not prodnd:
                    # raise Exception("No product found")
                    continue
                iii = iii+1
                
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['Brand'] = self.get_text_by_path(nd, './/div[@class="product-box__brand"]/text()')
                dd['Title'] = self.get_text_by_path(nd, './/div[@class="product-box__name"]/text()')
                produrl = self.get_text_by_path(nd, './/a[@class="product-box__title"]/@href')
                # --produrl(/sneakers_homme_derby-le_coq_sportif-p-242284542E/)-
                urlsplit = produrl.split('_')
                if len(urlsplit) > 1:
                    dd['Category'] = urlsplit[0].replace('/', ' ')
                dd['Url'] = self.get_site_url(produrl)
                img = self.get_text_by_path(nd, './/img/@src') # nd.xpath('.//img/@src').get()
                dd['Thumbnail'] = self.get_site_url(img) if img else None
                reviewstr = self.get_text_by_path(nd, './/div[@class="product-box__avis"]/text()[normalize-space()]')
                dd['TotalReviewsText'] = reviewstr if reviewstr else None
                # self.lg.debug(f"--------parse_list__nd({iii})--reviewstr({reviewstr})--")
                dd['TotalReviews'] = int(reviewstr.replace(' avis', '').replace(' ', '').replace(' ', '')) if reviewstr else 0
                pricetext = self.get_text_by_path(nd, './/span[@class="product-box__price--normal"]/text()')
                oldpricetext = ""
                if pricetext:
                    oldpricetext = pricetext
                else:
                    pricetext = self.get_text_by_path(nd, './/span[@class="product-box__price--alert"]/text()')
                    oldpricetext = self.get_text_by_path(nd, './/span[@class="product-box__price--crossed"]/del/text()')
                dd['PriceText'] = pricetext
                dd['OldPriceText'] = oldpricetext
                self.lg.debug(f"-----parse_list---item---produrl({produrl})--urlsplit({urlsplit})---reviewstr({reviewstr})---pricetext({pricetext})---oldpricetext({oldpricetext})--")
                dd['FinalPrice'] = float(pricetext.replace('€', '').replace(' ', '').replace(',', '.')) if pricetext else 0   # self.get_price(pricetext)
                dd['OldPrice'] = float(oldpricetext.replace('€', '').replace(' ', '').replace(',', '.')) if oldpricetext else 0 # self.get_price(oldpricetext)
                if ['OldPrice'] == 0:
                    dd['OldPrice'] = dd['FinalPrice']
                # self.lg.debug(f"-----parse_list---item---dd({dd})---")
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            requrl = ""
            if page * self.page_size < total_count:
                requrl = response.request.url
                if "?page=" in requrl:
                    requrl = requrl.replace(f"?page={page-1}", f"?page={page}")
                else:
                    if page > 1:
                        raise Exception("error page > 1 requrl:"+requrl)
                    requrl = requrl + "?page=1"
            dl = {'PageSize': self.page_size, 'TotalCount': total_count, 'ProductList': prods, 'NextPageUrl': requrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            # dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield dd
            # yield Request(dd['Url'], self.parse_detail, meta=dict(browser=True, page=page, dd=dd, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))

        if dl['NextPageUrl'] != "" or len(prods) == self.page_size:
            self.lg.debug(f"---Begin--Request--next_page--{dl['NextPageUrl']}---")
            nextmeta = dict(browser=True, 
                            # do_not_request=True,
                            scroll_down=500, wait_element='xpath://div[@id="product__container"]/article[1]', 
                            scroll_times=8,
                            # click_element='xpath://a[@aria-label="Page suivante"]', 
                            page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=nextmeta)
