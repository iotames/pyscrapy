from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
import json


class YsabelmoraSpider(BaseSpider):

    name = "ysabelmora"
    base_url = "https://ysabelmora.com"
    allowed_domains = ["ysabelmora.com"]
    start_urls_group = [
        {'index': 1, 'title': 'Women', 'name':'mujer', 'code': '23801381519690', 'url': 'https://ysabelmora.com/collections/mujer'},
        {'index': 2, 'title': 'Man', 'name':'hombre', 'code': '23871704891722', 'url': 'https://ysabelmora.com/collections/hombre'},
        {'index': 3, 'title': 'Baby', 'name':'bebe', 'code': '23871499338058', 'url': 'https://ysabelmora.com/collections/bebe'}, # 326 products
        {'index': 4, 'title': 'Niña', 'name':'nina', 'code': '23878733398346', 'url': 'https://ysabelmora.com/collections/nina'},
        {'index': 5, 'title': 'Niño', 'name':'nino', 'code': '23879504691530', 'url': 'https://ysabelmora.com/collections/nino'}, 
        {'index': 6, 'title': 'Teen', 'name':'teen', 'code': '23931583529290', 'url': 'https://ysabelmora.com/collections/teen'},
    ]
    # start_urls = []


    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Brand', 'Category', 'Code', 'Title', 'PriceText', 'FinalPrice', 'OldPrice', 'SizeList', 'SizeNum', 'Material', 'Description', 'Url', 'Image']
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'ysabelmora.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        group_code = gp.get('code')
        groupIndex = gp.get('index')
        requrl = "https://ysabelmora.com/collections/{}?section_id=template--{}__main".format(group_name, group_code)
        referer = gp.get('url')
        if pageindex > 1:
            requrl = "https://ysabelmora.com/collections/{}?page={}&section_id=template--{}__main".format(group_name, pageindex, group_code)
            referer = "{}?page={}".format(gp.get('url'), pageindex)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 28
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
            next_page_url = dl['NextPageUrl']
            page_index = dl['PageIndex']
            has_next_page = True if next_page_url is not None else False
        else:
            # 提取商品列表
            nds = response.xpath('//product-list/product-wrapper')
            next_url = self.get_text_by_path(response, '//a[@rel="next"]/@href')
       
            if next_url is not None:
                has_next_page = True
                next_url = self.base_url + next_url

            dl = {'Url': gp.get('url'), 'NextPageUrl': next_url, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
   
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
                img = self.get_text_by_path(nd, './/a[@class="product-card__media"]/img/@src')
                if img is not None:
                    img = 'https:' + img
                    dd['Image'] = img
                    dd['Thumbnail'] = img.replace('width=1533', 'width=400').replace('height=1534', 'height=400')
                
                # 提取商品URL  
                url = self.get_text_by_path(nd, './/a[@class="product-card__media"]/@href')
                dd['Url'] = self.base_url + url

                title = self.get_text_by_path(nd, './/h2[@class="product-title  line-clamp"]/a/text()')
                dd['Title'] =title

                # 价格提取部分
                sale_price_text = self.get_text_by_path(nd, './/price-list/sale-price/text()[2]')
                dd['PriceText'] = sale_price_text
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None

                # 原价提取（如果有）
                old_price_text = self.get_text_by_path(nd, './/price-list/compare-at-price/text()[2]')
                dd['OldPriceText'] = old_price_text
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else dd['FinalPrice']
                print(f"----sale_price_text({sale_price_text})---old_price_text({old_price_text})-FinalPrice({dd['FinalPrice']})--OldPrice({dd['OldPrice']})---({self.get_text_by_path(nd, './/price-list/sale-price/span/text()')})---")

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
            sku_text = self.get_text_by_path(response, '//variant-sku/text()')
            dd['Code'] = sku_text.replace('SKU: ', '') if sku_text else None

            # 提取 JSON 字符串
            script_text = self.get_text_by_path(response, '//script[@type="application/ld+json"]/text()')
            if script_text is not None:
                dd['DataRaw'] = script_text
                jsdata = json.loads(script_text)
                size_list = []
                for off in jsdata['offers']:
                    size_list.append(off['name'])
                dd['SizeList'] = size_list
                dd['SizeNum'] = len(dd['SizeList'])
                # dd['PublishedAt'] = jsdata['published_at']
                desc = jsdata['description']
                dd['Description'] = desc
                mtlist = get_material(desc)
                if len(mtlist) > 0:
                    dd['Material'] = ";".join(mtlist)
                # dd['FinalPrice'] = float(jsdata['price']/100)
                # dd['OldPrice'] = float(jsdata['compare_at_price']/100) if jsdata['compare_at_price'] else dd['FinalPrice']
                dd['Category'] = jsdata['category']
                dd['Title'] = jsdata['name']
                dd['Brand'] = jsdata.get('brand', {}).get('name', '')
            yield dd

    def get_price_by_text(self, price_text: str) -> float:
        if not price_text:
            return 0.0
        
        # 处理欧洲价格格式（如：6,95 €）
        price_str = price_text.replace('€', '').replace(',', '.').strip()
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0