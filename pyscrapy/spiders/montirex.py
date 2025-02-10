from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
import re


class MontirexSpider(BaseSpider):
    name = "montirex"
    base_url = "https://montirex.com"
    allowed_domains = ["montirex.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8

        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Title', 
                               'PriceText', 'FinalPrice', 'OldPrice', 'Discount', 'Tags', 'SizeList', 'SizeNum', 'Material', 'Description', 'Url']
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'montirex.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        # https://montirex.com/en-us/collections/all-products?page=4&section_id=template--24421232443769__main
        {'index': 1, 'title': "ALL MEN'S CLOTHING", 'name':'all-products', 'code': '24421232443769', 'url': 'https://montirex.com/en-us/collections/all-products'}, # 261 products 
        # # https://montirex.com/en-us/collections/all-womens-clothing?page=3&section_id=template--24421232542073__main
        {'index': 2, 'title': "ALL WOMEN'S CLOTHING", 'name':'all-womens-clothing', 'code': '24421232542073', 'url': 'https://montirex.com/en-us/collections/all-womens-clothing'}, # 143 products
        # # https://montirex.com/en-us/collections/boys-all-products?page=2&section_id=template--24421232312697__main
        {'index': 3, 'title': "ALL BOYS CLOTHING", 'name':'boys-all-products', 'code': '24421232312697', 'url': 'https://montirex.com/en-us/collections/boys-all-products'}, # 113 products
        {'index': 4, 'title': "ALL GIRLS CLOTHING", 'name':'all-girls-products', 'code': '', 'url': 'https://montirex.com/en-us/collections/all-girls-products'}, # 39 products
    ]

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        group_code = gp.get('code')
        groupIndex = gp.get('index')
        requrl = "https://montirex.com/en-us/collections/{}?page={}&section_id=template--{}__main".format(group_name, pageindex, group_code)
        referer = "{}?page={}".format(gp.get('url'), pageindex)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            # 'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            # 'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        if group_name == "all-girls-products":
            requrl = gp.get('url')
            hdr['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        else:
            hdr['accept'] = '*/*'
            hdr['referer'] = referer
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 48
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
            nds = response.xpath('//product-item')
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
                img = self.get_text_by_path(nd, './/img[@class="product-item__primary-image"]/@src')
                if img is not None:
                    img = 'https:' + img
                    dd['Thumbnail'] = img
                
                # 提取商品URL  
                purl = self.get_text_by_path(nd, './/a[@class="product-item-meta__title"]/@href')
                dd['Url'] = self.base_url + purl

                tags = []
                bdgnds = nd.xpath('.//div[@class="product-item__label-list label-list"]/span/text()')
                if bdgnds is not None:
                    labels = bdgnds.getall()
                    if len(labels) > 0:
                        for label in labels:
                            tags.append(label)
                dd['Tags'] = tags

                title = self.get_text_by_path(nd, './/a[@class="product-item-meta__title"]/text()')
                dd['Title'] =title
                if title is not None:
                    titlesplit = title.split(' - ')
                    if len(titlesplit) > 1:
                        dd['Category'] = titlesplit[0]
                        dd['Tags'].append(titlesplit[0])
                
                # 价格提取部分
                sale_price_text = self.get_text_by_path(nd, './/span[@class="price"]/text()[2]')
                dd['PriceText'] = sale_price_text
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None

                print(f"----sale_price_text({sale_price_text})---FinalPrice({dd['FinalPrice']})----")

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
            dd['Discount'] = 0
            dd['OldPriceText'] = self.get_text_by_path(response, '//div[@class="price-list"]/span[@class="price price--compare"]/text()[2]')
            if dd['OldPriceText'] is not None:
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText'])
                dd['PriceText'] = self.get_text_by_path(response, '//div[@class="price-list"]/span[@class="price price--highlight price--large"]/text()[2]')
                if dd['PriceText'] is not None:
                    dd['FinalPrice'] = self.get_price_by_text(dd['PriceText'])
                inputmsg = "--------OldPriceText({})----OldPrice({})---PriceText({})--FinalPrice({})---".format(dd['OldPriceText'], dd['OldPrice'], dd['PriceText'], dd['FinalPrice'])
                print(inputmsg)
                dd['Discount'] = round((dd['OldPrice'] - dd['FinalPrice']) / dd['OldPrice'] * 100, 2)
            else:
                dd['OldPrice'] = dd['FinalPrice']
            desc = self.get_text_by_path(response, '//meta[@name="twitter:description"]/@content')
            dd['Description'] = desc
            if desc is not None:
                mtlist = get_material(desc)
                if len(mtlist) > 0:
                    dd['Material'] = ";".join(mtlist)
            sznds = response.xpath('//div[@class="block-swatch-list"]//label/text()')
            if sznds is not None:
                szlist = sznds.getall()
                szlist111 = []
                for sz in szlist:
                    szlist111.append(sz.strip())
                dd['SizeList'] = szlist111
                dd['SizeNum'] = len(szlist111)

            # 原始字符串
            s = response.text
            # 使用正则表达式匹配
            match = re.search(r',"category":"(.*?)",', s)
            if match:
                category = match.group(1)
                dd['Tags'].append(category)
                dd['Category'] = category
                print("------找到匹配项---------", category)  # 输出：Men's T-Shirts

            else:
                print("------------未找到匹配项-------------------", dd['Url'])
            yield dd