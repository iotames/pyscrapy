from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
import re


class IntersportseSpider(BaseSpider):
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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Brand', 'Title', 'PriceText', 'OldPrice', 'FinalPrice', 'TotalReviews', 'Tags', 'SizeList', 'SizeNum', 'Url'],
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
            self.lg.debug(f"--------------TotalStr:{totalStr}------")
            total_count = int(totalStr.replace(' produits', '').replace(' ', '')) if totalStr else 0
            iii = 0
            for nd in nds:
                iii = iii+1
                print(f"---------parse_list__nd({iii})-----")
                # /
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                prodnd = nd.xpath('div[@class="product-box"]')
                if not prodnd:
                    raise Exception("No product found")
        
                # brand = nd.xpath()  # brand.get().strip() if brand else ''
                dd['Brand'] = self.get_text_by_path(nd, './/div[@class="product-box__brand"]/text()')
                dd['Title'] = self.get_text_by_path(nd, './/div[@class="product-box__name"]/text()')
                produrl = self.get_text_by_path(nd, './/a[@class="product-box__title"]/@href')
                urlsplit = produrl.split('_')
                if len(urlsplit) > 1:
                    dd['Category'] = urlsplit[0].replace('/', ' ')
                dd['Url'] = self.get_site_url(produrl)
                # dd['Thumbnail'] = nd.xpath('.//img/@src').get()
                # reviewstr = self.get_text_by_path(nd, './/div[@class="rating-v2"]/span[2]/text()')
                # dd['TotalReviewsText'] = reviewstr if reviewstr else None
                # dd['TotalReviews'] = int(reviewstr.replace('(', '').replace(')', '').replace(',', '').replace(' ', '')) if reviewstr else 0  # (103)
                # dd['PriceText'] = self.get_text_by_path(nd, './/span[@class="price-tag price-tag-current"]/text()')
                # pricestr = self.get_text_by_path(nd, './/span[@class="price-tag price-tag-current"]/text()')
                # # 299 kr
                # if pricestr:
                #     if pricestr.find('kr') > 0:
                #         pricestr = pricestr.replace(' kr', '')
                #     dd['FinalPrice'] = float(pricestr) if pricestr else 0
                # oldPricestr = self.get_text_by_path(nd, './/span[@class="price-tag price-tag-original"]/text()')
                # if oldPricestr:
                #     if oldPricestr.find('kr') > 0:
                #         oldPricestr = oldPricestr.replace(' kr', '')
                #     dd['OldPrice'] = float(oldPricestr) if oldPricestr else dd['FinalPrice']
                # # self.lg.debug(f"-----reviewstr({reviewstr})---pricestr---{pricestr}---oldPrice-{oldPricestr}")
                # tagstr = self.get_text_by_path(nd, './/div[@class="product-card__category"]/text()')
                # dd['Tags'] = [item.strip() for item in tagstr.strip().split(',')] if tagstr else []
                # bdgs = nd.xpath('.//div[@data-testid="product-badge"]')
                # for bd in bdgs:
                #     bd_text = bd.xpath('text()').extract_first()
                #     if bd_text:
                #         dd['Tags'].append(bd_text.strip())
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            requrl = ""
            if page * self.page_size < total_count:
                requrl = response.request.url
                if "?p=" in requrl:
                    requrl = requrl.replace(f"?page={page-1}", f"?p={page}")
                else:
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
                            scroll_down=500, wait_element='xpath://div[@data-sentry-source-file="ProductsGroup.tsx"]/article[4]//div[@class="product-card__title"]//a[2]', 
                            scroll_times=8,
                            click_element='xpath://button[@class="btn btn-icon-only btn-nav"][2]', 
                            page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=nextmeta)
