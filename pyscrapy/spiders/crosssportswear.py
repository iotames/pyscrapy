from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
import time
from urllib.parse import quote


class CrosssportswearSpider(BaseSpider):

    name = "crosssportswear"
    base_url = "https://www.cross-sportswear.com"
    allowed_domains = ["services.mybcapps.com","www.cross-sportswear.com"]

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
        'FEED_EXPORT_FIELDS': [
            'Thumbnail', 'Category', 'Gender', 'PublishedAt', 'Brand', 'Title', 'PriceText',
            'OldPrice', 'FinalPrice', 'TotalInventoryQuantity', 'SizeNum', 'SizeList','Tags', 
            'Material', 'Description', 'Image', 'Url'
        ],
        # 'FEED_EXPORT_FIELDS_DICT': {"TotalInventoryQuantity": "库存数"}
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'crosssportswear.xlsx',
        # 'FEED_FORMAT': 'xlsx'
        }

    start_urls_group = [
        {'index': 1, 'title': 'All Products', 'name':'all', 'code':'0','url': 'https://www.cross-sportswear.com/collections/all'}, # 215
    ]

    # start_urls = []

    @staticmethod
    def get_data_dict(data: dict) ->dict:
        title_split = data.get('Title').split(' ')
        if len(title_split) > 1:
            title1 = title_split[0]
            if title1 in ["M/W", "M", "W"]:
                data['Gender'] = title1
        return data

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        referer = self.base_url + "/"
        groupIndex = gp.get('index')
        sid = "cd2b84e7-115e-4538-8661-ef56c0362226"
        reqarg = "t={}&_=pf&shop=cross-sportswear-intl.myshopify.com&page={}&limit={}&sort=title-ascending&locale=en&event_type=init&build_filter_tree=true&sid={}&pg=collection_page&zero_options=true&product_available=false&variant_available=false&urlScheme=2&collection_scope={}".format(int(time.time()*1000),pageindex, self.page_size, sid, gp.get('name'))
        requrl = "https://services.mybcapps.com/bc-sf-filter/filter?{}".format(reqarg)
        logmsg = f"----request_list_by_group--group({gp['title']})({group_name})--pageindex({pageindex})--url:({requrl})--"
        print(logmsg)
        hdr = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': self.base_url,
            'priority': 'u=1, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

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
            total_count = dl['TotalCount']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page_index, total_count)
        else:
            result = response.json()
            total_count = result.get('total_product', 0)
            page_index = page
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            dd_list = result.get('products', [])
            if len(dd_list) == 0:
                raise ValueError("products is empty")
            prods = []
            for d in dd_list:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                urlkey = d.get('handle')
                dd['UrlKey'] = urlkey
                if dd['UrlKey'] is None:
                    continue
                dd['Url'] = "{}/products/{}".format(self.base_url, urlkey)
                final_price = float(d.get("price_min_sek", 0))
                compare_at_price = d.get("compare_at_price_min_sek", 0)
                dd['PriceText'] = "{} SEK".format(final_price)
                dd['FinalPrice'] = final_price
                if compare_at_price is not None and compare_at_price > 0:
                    dd['OldPrice'] = float(compare_at_price)
                dd['Description'] = d.get('body_html', '')
                imgs = d.get('images', {})
                if len(imgs) > 0:
                    dd['Image'] = imgs["1"]
                    dd['Thumbnail'] = imgs["1"] + "&width=400"
                    dd['image_urls'] = [dd['Thumbnail']]
                options_with_values = d.get('options_with_values', [])
                size_list = []
                if options_with_values is not None:
                    for optv in options_with_values:
                        if optv['name'] == 'size':
                            for v in optv.get('values', []):
                                size_list.append(v.get('title', ''))
                dd['SizeList'] = size_list
                dd['SizeNum'] = len(dd['SizeList'])                    
                dd['Category'] = d.get('product_type')
                dd['PublishedAt'] = d.get('published_at')
                dd['Tags'] = d.get('tags', [])
                dd['Title'] = d.get('title')
                dd['Brand'] = d.get('vendor')
                d_nodes = d.get('variants', [])
                variants = []
                total_qty = 0
                for d_node in d_nodes:
                    qty = d_node['inventory_quantity']
                    total_qty += qty
                    variants.append({'Code': d_node['sku'], 'Title': d_node['title'], 'Quantity': qty})
                dd['Variants'] = variants
                dd['TotalInventoryQuantity'] = total_qty
                materials = get_material(dd['Description'])
                dd['Material'] = ",".join(materials)
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
