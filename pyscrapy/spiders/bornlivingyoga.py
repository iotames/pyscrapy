from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
from datetime import datetime, timedelta
from sqlalchemy import and_
import json
import re


class BornlivingyogaSpider(BaseSpider):
    name = "bornlivingyoga"
    base_url = "https://bornlivingyoga.com"
    allowed_domains = ["bornlivingyoga.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8

        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'PublishedAt', 'Category', 'Title', 'PriceText', 'FinalPrice', 'OldPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url']
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'bornlivingyoga.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': "All Products", 'name':'all', 'code': 'all', 'url': 'https://bornlivingyoga.com/collections/all'},
    ]

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        groupIndex = gp.get('index')
        requrl = "https://bornlivingyoga.com/collections/{}?page={}".format(group_name, pageindex)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 128
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)
    
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
            has_next_page = self.check_next_page(page, total_page)
        else:
            # 提取商品列表
            total_page_str = self.get_text_by_path(response, '//li[@class="pagination__item"][last()]/a/text()')
            total_page = int(total_page_str)
            has_next_page = self.check_next_page(page, total_page)
            dl = {'Url': gp.get('url'), 'TotalPage': total_page, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}

            nds = response.xpath('//div[@data-limoniapps-discountninja-product-handle]')
            if nds is None or len(nds) == 0:
                # raise ValueError("models is empty")
                return
            
            prods = []
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                page_index = page
                dd['PageIndex'] = page_index

                # 提取缩略图
                img = self.get_text_by_path(nd, './/img/@src')
                if img is not None:
                    dd['Thumbnail'] = 'https:' + img
                
                tags = []
                dd['UrlKey'] = nd.xpath('@data-limoniapps-discountninja-product-handle').get()
                tags_val = nd.xpath('@data-limoniapps-discountninja-product-tags')
                if tags_val is not None:
                    tags = tags_val.get().split(',')

                badges = nd.xpath('.//div[@class="label"]/div[@class="label--percentage"]/text()').getall()
                if badges is not None and len(badges) > 0:    
                    for bdg in badges:
                        tags.append(bdg.strip())
                dd['Tags'] = tags

                # 提取商品URL
                purl = self.get_text_by_path(nd, './/h3[@class="product-item__title"]/a/@href')
                dd['Url'] = self.get_site_url(purl) if purl is not None else None
                dd['Title'] = self.get_text_by_path(nd, './/h3[@class="product-item__title"]/a/text()')

                # 价格提取部分
                dd['PriceText'] = self.get_text_by_path(nd, './/span[@class="product-item__price"]/text()')
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                
                print(f"----sale_price_text({dd['PriceText']})---FinalPrice({dd['FinalPrice']})--Url({dd['Url']})--")

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
            # yield prod
            prod['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield Request(prod['Url'], self.parse_detail, meta=dict(dd=prod, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
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
            dd['Category'] = self.get_text_by_path(response, '//ul[@itemtype="https://schema.org/BreadcrumbList"]/li[last()]//span[@itemprop="name"]/text()')

            desnds = response.xpath('//div[@class="shpflt-product__info__extra__tab__content"]/div/text()')
            if desnds is not None:
                for desnd in desnds.getall():
                    print(f"--------purl({dd['Url']})--------")
                    if desnd.find("%") >= 0:
                        mtlist = get_material(desnd)
                        if len(mtlist) > 0:
                            dd['Material'] = ";".join(mtlist)
                            break

# {"id":6535219675230,"title":"Shirt Halia Zen Blue","handle":"shirt-halia-zen-blue","description":"\u003cp\u003eCamiseta manga corta. Cuello redondo. Tejido seamless sin costuras para un mayor confort. Camiseta con corte por la cintura.\u003c\/p\u003e\n\u003cul\u003e\n\u003cli\u003eTejido 4 Way Stretch\u003c\/li\u003e\n\u003cli\u003eHigh solar protector\u003c\/li\u003e\n\u003cli\u003eNatural fibers\u003c\/li\u003e\n\u003cli\u003eSeamless\u003c\/li\u003e\n\u003cli\u003eSoft touch\u003c\/li\u003e\n\u003cli\u003eAnti-Bacterial\u003c\/li\u003e\n\u003cli\u003eAnti-Static\u003c\/li\u003e\n\u003c\/ul\u003e","published_at":"2024-11-24T18:34:35+01:00","created_at":"2021-02-24T10:55:52+01:00","vendor":"BORN","type":"Camisetas","tags":["Barre","blue","Camisetas","L","manga-corta","Mujer","Rebajas","S","Seamless","TBBORNDIC24","thebraderyjune24","THEBRADERYSEPT24"],"price":2490,"price_min":2490,"price_max":2490,"available":true,"price_varies":false,"compare_at_price":2490,"compare_at_price_min":2490,"compare_at_price_max":2490,"compare_at_price_varies":false,"variants":[{"id":39246031585374,"title":"S","option1":"S","option2":null,"option3":null,"sku":"8435584622508","requires_shipping":true,"taxable":true,"featured_image":null,"available":true,"name":"Shirt Halia Zen Blue - S","public_title":"S","options":["S"],"price":2490,"weight":0,"compare_at_price":2490,"inventory_quantity":86,"inventory_management":"shopify","inventory_policy":"deny","barcode":"8435584622508","requires_selling_plan":false,"selling_plan_allocations":[],"quantity_rule":{"min":1,"max":null,"increment":1}},{"id":39246031618142,"title":"M","option1":"M","option2":null,"option3":null,"sku":"8435584622560","requires_shipping":true,"taxable":true,"featured_image":null,"available":false,"name":"Shirt Halia Zen Blue - M","public_title":"M","options":["M"],"price":2490,"weight":0,"compare_at_price":2490,"inventory_quantity":0,"inventory_management":"shopify","inventory_policy":"deny","barcode":"8435584622560","requires_selling_plan":false,"selling_plan_allocations":[],"quantity_rule":{"min":1,"max":null,"increment":1}},{"id":39246031650910,"title":"L","option1":"L","option2":null,"option3":null,"sku":"8435584622621","requires_shipping":true,"taxable":true,"featured_image":null,"available":true,"name":"Shirt Halia Zen Blue - L","public_title":"L","options":["L"],"price":2490,"weight":0,"compare_at_price":2490,"inventory_quantity":57,"inventory_management":"shopify","inventory_policy":"deny","barcode":"8435584622621","requires_selling_plan":false,"selling_plan_allocations":[],"quantity_rule":{"min":1,"max":null,"increment":1}}],"images":["\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1222.jpg?v=1739748229","\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1233.jpg?v=1739748230"],"featured_image":"\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1222.jpg?v=1739748229","options":["Talla"],"media":[{"alt":null,"id":21126744113246,"position":1,"preview_image":{"aspect_ratio":0.75,"height":2074,"width":1555,"src":"\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1222.jpg?v=1739748229"},"aspect_ratio":0.75,"height":2074,"media_type":"image","src":"\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1222.jpg?v=1739748229","width":1555},{"alt":null,"id":21126744178782,"position":2,"preview_image":{"aspect_ratio":0.75,"height":2135,"width":1601,"src":"\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1233.jpg?v=1739748230"},"aspect_ratio":0.75,"height":2135,"media_type":"image","src":"\/\/bornlivingyoga.com\/cdn\/shop\/products\/Born3-3-22-1233.jpg?v=1739748230","width":1601}],"requires_selling_plan":false,"selling_plan_groups":[],"content":"\u003cp\u003eCamiseta manga corta. Cuello redondo. Tejido seamless sin costuras para un mayor confort. Camiseta con corte por la cintura.\u003c\/p\u003e\n\u003cul\u003e\n\u003cli\u003eTejido 4 Way Stretch\u003c\/li\u003e\n\u003cli\u003eHigh solar protector\u003c\/li\u003e\n\u003cli\u003eNatural fibers\u003c\/li\u003e\n\u003cli\u003eSeamless\u003c\/li\u003e\n\u003cli\u003eSoft touch\u003c\/li\u003e\n\u003cli\u003eAnti-Bacterial\u003c\/li\u003e\n\u003cli\u003eAnti-Static\u003c\/li\u003e\n\u003c\/ul\u003e"}

            try:
                # 解析 inventory_quantity 信息
                pattern = r'var\s+product\s*=\s*([^\n;]+)'
                match = re.search(pattern, response.text)
                jsonstr = match.group(1).strip() if match else None
                if jsonstr is not None:
                    dd['DataRaw'] = jsonstr
                    json_data = json.loads(jsonstr)
                    total_qty = 0
                    size_list = []
                    for variant in json_data['variants']:
                        size_list.append(variant.get('title', ''))
                        total_qty += variant.get('inventory_quantity', 0)
                    dd['TotalInventoryQuantity'] = total_qty
                    dd['SizeList'] = size_list
                    dd['SizeNum'] = len(size_list)
                    dd['PublishedAt'] = json_data.get('published_at', '')
                    dd['Description'] = json_data.get('description', '')
                    dd['FinalPrice'] = float(json_data.get('price_min', 0)/100)
                    dd['OldPrice'] = float(json_data.get('compare_at_price_max', 0)/100)
                    dd['Image'] = 'https:' + json_data.get('featured_image', '')
            except Exception as e:
                dd['TotalInventoryQuantity'] = 0
            yield dd

    def check_next_page(self, page_index, total_page):
        return page_index < total_page

    @classmethod
    def get_export_data(cls) -> list:
        step = 0
        data_list = []
        select_fields = [UrlRequest.data_format, UrlRequest.collected_at]
        reqs = UrlRequest.query(select_fields).filter(and_(
            UrlRequest.site_id == cls.get_site_id(),
            UrlRequest.collected_at > (datetime.now() - timedelta(hours=23)),
            UrlRequest.step == step
            )).all()
        if step == 0:
            for req in reqs:
                dd = req.data_format
                if 'OldPrice' not in dd:
                    dd['OldPrice'] = dd['FinalPrice']
                if dd['OldPrice'] is None:
                    dd['OldPrice'] = dd['FinalPrice']
                data_list.append(dd)
        if step == 1:
            for req in reqs:
                dl = req.data_format.get('ProductList', None)
                if dl is None:
                    raise Exception("ProductList could not be None")
                for dd in dl:
                    data_list.append(dd)
        return data_list
