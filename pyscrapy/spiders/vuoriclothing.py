from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from urllib.parse import quote
import json


class VuoriclothingSpider(BaseSpider):

    name = "vuoriclothing"
    base_url = "https://vuoriclothing.com"
    allowed_domains = ["vuoriclothing.com","p2mlbkgfds-dsn.algolia.net"]

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
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "GroupName", "Category",
        "Title", 'SubTitle', "Color", 'ColorNum', "FinalPrice", 'OldPrice', "TotalReviews", "ReviewRating", "TotalInventoryQuantity",
        "SizeNum", "SizeList", "Material", "Image", "Url"],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'vuoriclothing.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': "Women's Hoodies and Sweatshirts", 'name': 'womens-hoodies-and-sweatshirts', 'url': 'https://vuoriclothing.com/collections/womens-hoodies-and-sweatshirts', 'total': 61},
        {'index': 2, 'title': "Men's Hoodies and Sweatshirts", 'name': 'mens-hoodies-and-sweatshirts', 'url': 'https://vuoriclothing.com/collections/mens-hoodies-and-sweatshirts', 'total': 37},
    ]
    # start_urls = []

    def urlencode(self, txt:str) ->str:
        return quote(txt, safe="().-")

    def request_list_by_group(self, gp: dict, pageindex: int):
        x_algolia_agent="Algolia for JavaScript (4.24.0); Browser; instantsearch.js (4.73.1); react (18.3.1); react-instantsearch (7.12.1); react-instantsearch-core (7.12.1); next.js (14.2.15); JS Helper (3.22.2)"
        requrl = "https://p2mlbkgfds-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent={}".format(quote(x_algolia_agent, safe="().-"))

        groupIndex = gp.get('index')
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex={pageindex}--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']

        hdr = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': self.base_url,
            'Referer': "{}/".format(self.base_url),
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'x-algolia-api-key': '7825c979763a41aae103633f760004f1',
            'x-algolia-application-id': 'P2MLBKGFDS'
        }
        # 根据 gp['name'] 动态设置 collections 参数
        gpname = gp.get('name')
        user_token = "anonymous-46d3de0a-f424-4f1d-8620-ca21745535c9"
        params1 = "clickAnalytics=true&userToken={}".format(user_token)

        attributesToRetrieve = '["objectID","title","handle","image","variants_min_price","product_type","variants","online_inventory_available_by_option","tags","family_products","named_tags"]'
        facets = '["named_tags.category","named_tags.color-group","named_tags.fabric","named_tags.fit","named_tags.gender","named_tags.inseam","named_tags.length","named_tags.lined","named_tags.prod-usage","named_tags.support","options_available_online.Size"]'
        filters = f"(requires_shipping:false OR online_inventory_available:true OR tags:back-in-stock-enabled) AND NOT tags:findify-remove AND collections:{gpname} AND NOT named_tags.gated:internal-influencer-accepted AND NOT named_tags.gated:influencer-accepted"
        params2 = 'attributesToRetrieve={}&clickAnalytics=true&facets={}&filters={}&highlightPostTag=__/ais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=48&maxValuesPerFacet=50&page=1&userToken={}'.format(self.urlencode(attributesToRetrieve), self.urlencode(facets), self.urlencode(filters), user_token)
        postdata = '{"requests":[{"indexName":"us_products","params":"' + params1 + '"}, {"indexName":"us_products","params":"' + params2 + '"}]}'
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        return Request(requrl, callback=self.parse_list, method='POST', meta=meta, headers=hdr, body=postdata)

    def start_requests(self):
        self.page_size = 48
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
            dd_list = prods
            total_page = dl['TotalPage']
            total_count = dl['TotalCount']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_count)
        else:
            resultraw = response.json()
            resultlen = len(resultraw.get('results', []))
            if resultlen == 0:
                raise ValueError("results is empty")
            okresult = False
            result = {}
            for rev in resultraw.get('results', []):
                if rev.get('index') == 'us_products':
                    if gp.get('total', 0) == rev.get('nbHits', 0):
                    # if rev.get('params', '').startswith("attributesToRetrieve="):
                        okresult = True
                        result = rev
            if okresult == False:
                raise ValueError("result not fount")
            # result = result['results'][resultlen-1]
            total_count = result['nbHits']
            page_index = result['page']+1
            # hitsPerPage pageSize
            total_page = result['nbPages']
            # if page_index != page:
            #     self.lg.debug(f"-------parse_list--page_index({page_index})--page({page})----resultraw({resultraw})--------result({result})--")
            #     raise ValueError("page index not match")
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            hits = result['hits']
            if hits is None or len(hits) == 0:
                with open("{}.list.json".format(self.name), "w", encoding="utf-8") as file:
                    file.write(response.text)
                raise ValueError("hits is empty")
            prods = []
            dd_list = []
            for d in hits:
                urlKey = d.get('handle', '')
                if urlKey == "":
                    continue
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                dd['Code'] = d.get('objectID')
                dd['Category'] = d.get('product_type')
                dd['Title'] = d.get('title')
                dd['FinalPrice'] = d.get("variants_min_price")
                img = d.get('image')
                dd['Image'] = img
                dd['Thumbnail'] = img + "&width=200"
                dd['image_urls'] = [img]
                dd['UrlKey'] = urlKey
                dd['Url'] = f"{self.base_url}/products/{urlKey}"
                dd['Tags'] = d.get('tags', [])
                size_num = len(d.get("variants"))
                size_list = []
                for vv in d.get("variants"):
                    size_list.append(vv.get("options").get("Size"))
                total_inventory_quantity = 0
                color = ''
                variants = []
                if 'online_inventory_available_by_option' in d:
                    totalqty = 0
                    if 'Color' in d['online_inventory_available_by_option']:
                        for k, v in d['online_inventory_available_by_option']['Color'].items():
                            color = k
                            totalqty = v.get("quantity", 0)
                    if 'Size' in d['online_inventory_available_by_option']:
                        for sz, qtyinfo in d['online_inventory_available_by_option']['Size'].items():
                            szqty = qtyinfo.get("quantity", 0)
                            total_inventory_quantity += szqty
                            variants.append({'Code': "", 'Title': sz, 'Quantity': szqty})
                    if totalqty != total_inventory_quantity:
                        raise ValueError("total_inventory_quantity not match")
                dd['Variants'] = variants
                dd['Color'] = color
                dd['SizeNum'] = size_num
                dd['TotalInventoryQuantity'] = total_inventory_quantity
                dd['SizeList'] = size_list
                gender = d.get('named_tags', {}).get('gender', [])
                if len(gender) > 0:
                    dd['Gender'] = ",".join(gender)
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
            newrequrl = dd['Url']
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
            jsonstr = self.get_text_by_path(response, '//script[@type="application/json"][@id="__NEXT_DATA__"]/text()')
            if jsonstr is None or jsonstr == "":
                self.lg.error(f"-----parse_detail--jsonstr is empty--requrl:{response.url}---")
                return
            result = json.loads(jsonstr)
            # .props.pageProps.pdpPageProps.structuredData.material
            structuredData = result.get('props', {}).get('pageProps', {}).get('pdpPageProps', {}).get('structuredData', {})
            dd['Material'] = structuredData.get('material', '')
            dd['ReviewRating'] = float(structuredData.get('aggregateRating', {}).get('ratingValue', 0))
            dd['TotalReviews'] = int(structuredData.get('aggregateRating', {}).get('reviewCount', 0))
            # .props.pageProps.pdpPageProps.variants
            variants = result.get('props', {}).get('pageProps', {}).get('pdpPageProps', {}).get('variants', [])
            for v in variants:
                selectedOptions = v.get('selectedOptions', [])
                for sele in selectedOptions:
                    if sele.get('name') == 'Color':
                        if sele.get('value') == dd['Color']:
                            dd['OldPrice'] = v.get('compareAtPrice')
                            dd['FinalPrice'] = v.get('price')
                            break
            # .props.pageProps.pdpPageProps.products
            colorprods = result.get('props', {}).get('pageProps', {}).get('pdpPageProps', {}).get('products', [])
            colornum = len(colorprods)
            for colorprod in colorprods:
                if dd['Color'] in colorprod.get('name'):
                    dd['SubTitle'] = colorprod.get('description')
            dd['ColorNum'] = colornum if colornum > 0 else 1
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}---result({result})--")
            dd['DataRaw'] = jsonstr
            yield dd
