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
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Brand', 'Code', 'Title', 'SubTitle', 'Color', 'OldPrice', 'FinalPrice', 'Tags', 'SizeList', 'SkuNum','Image', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'gymshark.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': 'Women', 'name':'womens', 'url': 'https://www.gymshark.com/collections/all-products/womens'},
        {'index': 2, 'title': 'Men', 'name':'mens', 'url': 'https://www.gymshark.com/collections/all-products/mens'},
    ]
    # start_urls = []

# https://www.gymshark.com/collections/all-products/womens?page=4
# https://www.gymshark.com/collections/all-products/mens?page=1

# curl 'https://www.gymshark.com/_next/data/TZZzobkOLiMV4N02tcmXy/en-US/collections/all-products/womens.json?collectionSlug=all-products&genderSlug=womens&page=4' \
#   -H 'accept: */*' \
#   -H 'accept-language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7' \
#   -H 'priority: u=1, i' \
#   -H 'referer: https://www.gymshark.com/collections/all-products/womens?page=3' \
#   -H 'sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Windows"' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36' \
#   -H 'x-nextjs-data: 1'

# begin with page=0
# curl 'https://www.gymshark.com/_next/data/TZZzobkOLiMV4N02tcmXy/en-US/collections/all-products/mens.json?collectionSlug=all-products&genderSlug=mens&page=1' \
#   -H 'priority: u=1, i' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Windows"' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'x-nextjs-data: 1'


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

    def check_next_page(self, page_index, total_count):
        return page_index * self.page_size < total_count

    def parse_list(self, response: TextResponse):
        meta = response.meta
        gp: dict = meta['gp']
        page = meta['page']
        groupName = gp.get('title')
        self.lg.debug(f"-------parse_list--page={page}----requrl({response.url})---")
        has_next_page = False

        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
            total_count = dl['TotalCount']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_count)
        else:
            result = response.json()
            total_count = result['listing']['pagination']['total']
            page_index = result['listing']['pagination']['page']
            if page_index != page:
                raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'TotalCount': total_count, 'Url': gp.get('url'), 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            models = result['listing']['models']
            if models is None or len(models) == 0:
                # raise ValueError("models is empty")
                return
            prods = []
            for m in models:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                dd['FinalPrice'] = m.get('price')
                dd['OldPrice'] = m.get('price_initial')
                dd['Title'] = m.get('name')
                dd['Brand'] = m.get('brand')
                dd['Code'] = m.get('code')
                dd['Color'] = m.get('color')
                dd['SubTitle'] = m.get('subhead')
                dd['Category'] = m.get('margin_segment')
                purl = m.get('url')
                if purl is None:
                    continue
                dd['Url'] = 'https://' + purl
                size_list = []
                vsv = m.get('products_summary')
                if vsv is not None:
                    for v in vsv:
                        size_list.append(v['size'])
                dd['SizeList'] = size_list
                dd['SizeNum'] = len(size_list)
                dd['SkuNum'] = len(m.get('skus'))
                dd['Tags'] = m.get('tags')
                dd['Gender'] = m.get('gender')
                if 'image' in m:
                    imgurl = "https://resize.sprintercdn.com/f/{}/{}?w={}&q=75".format("512x512", m['image']['file'], "512")
                    dd['Thumbnail'] = imgurl
                    dd['Image'] = imgurl
                    dd['image_urls'] = [imgurl]

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
            # yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        if has_next_page:
            self.lg.debug(f"-----parse_list--goto({gp.get('title')})--next_page({dl['PageIndex']+1})--")
            yield self.request_list_by_group(gp, page+1)

