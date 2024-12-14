from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from urllib.parse import quote


class GymsharkSpider(BaseSpider):

    name = "gymshark"
    base_url = "https://www.gymshark.com"
    allowed_domains = ["www.gymshark.com"]

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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Gender', 'Code', 'Title',  'Color', 'OldPrice', 'FinalPrice', 'Discount', 'TotalInventoryQuantity', 'TotalReviews', 'SizeNum', 'SizeList', 'Tags', 'Image', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'gymshark.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': 'Women', 'name':'womens', 'url': 'https://www.gymshark.com/collections/all-products/womens'},
        {'index': 2, 'title': 'Men', 'name':'mens', 'url': 'https://www.gymshark.com/collections/all-products/mens'},
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        requrl = "https://www.gymshark.com/_next/data/TZZzobkOLiMV4N02tcmXy/en-US/collections/all-products/{}.json?collectionSlug=all-products&genderSlug={}&page={}".format(group_name, group_name, pageindex-1)
        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex={pageindex}--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': gp.get('url'),
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
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
            total_count = result['pageProps']['prefetch']['nbHits']
            page_index = result['pageProps']['prefetch']['page'] + 1
            total_page = result['pageProps']['prefetch']['nbPages']
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_page)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            hits = result['pageProps']['prefetch']['hits']
            if hits is None or len(hits) == 0:
                # raise ValueError("models is empty")
                return
            prods = []
            for d in hits:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                availableSizes = d.get('availableSizes')
                if availableSizes is not None:
                    size_list = []
                    totalqty = 0
                    variants = []
                    for s in availableSizes:
                        totalqty += s['inventoryQuantity']
                        size_list.append(s['size'])
                        variants.append({'Code': s['sku'], 'Title': s['size'], 'Quantity': s['inventoryQuantity']})
                    dd['SizeList'] = size_list
                    dd['SizeNum'] = len(size_list)
                    dd['TotalInventoryQuantity'] = totalqty
                    dd['Variants'] = variants
                dd['Color'] = d.get('colour')
                dd['OldPrice'] = d.get('compareAtPrice')
                dd['Discount'] = d.get('discountPercentage', 0)
                imgurl = d.get('featuredMedia').get('src')
                dd['Image'] = imgurl
                dd['Thumbnail'] = imgurl + "&width=300"
                dd['image_urls'] = [imgurl]
                dd['Gender'] = d.get('gender')
                dd['UrlKey'] = d.get('handle')
                labels = d.get('labels')
                tags = []
                if labels is not None:
                    tags = labels
                dd['FinalPrice'] = d.get('price')
                if dd['OldPrice'] is None:
                    dd['OldPrice'] = dd['FinalPrice']
                if 'rating' in d:
                    dd['TotalReviews'] = d['rating'].get('count', 0)
                    dd['ReviewRating'] = d['rating'].get('average', 0)
                dd['Code'] = d.get('sku')
                dd['Title'] = d.get('title')
                dd['Category'] = d.get('type')
                if dd['UrlKey'] is None:
                    continue
                dd['Url'] = "{}/products/{}".format(self.base_url, dd['UrlKey'])
                dd['Tags'] = tags
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
            # dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            # yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        if has_next_page:
            self.lg.debug(f"-----parse_list--goto({gp.get('title')})--next_page({dl['PageIndex']+1})--")
            yield self.request_list_by_group(gp, page+1)

