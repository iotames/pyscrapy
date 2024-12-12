from models import UrlRequest, UrlRequestSnapshot
from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem, FromPage
import json
import re


class LippioutdoorSpider(BaseSpider):
    name = "lippioutdoor"
    base_url = "https://www.lippioutdoor.com"
    allowed_domains = ["www.lippioutdoor.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'PublishedAt', 'GroupName', 'Category', 'Brand', 'Title', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'Image', 'Description', 'Url']
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'lippioutdoor.xlsx',
        # 'FEED_FORMAT': 'xlsx',
    }


    start_urls_group = [
        {'index': 1, 'title': 'MAN', 'url': 'https://www.lippioutdoor.com/collections/hombre'},
        {'index': 2, 'title': 'WOMEN', 'url': 'https://www.lippioutdoor.com/collections/mujer'},
        {'index': 3, 'title': 'CHILDREN', 'url': 'https://www.lippioutdoor.com/collections/ninos'},
        {'index': 4, 'title': 'FOOTWEAR', 'url': 'https://www.lippioutdoor.com/collections/calzado'},
        {'index': 5, 'title': 'EQUIPMENT', 'url': 'https://www.lippioutdoor.com/collections/equipamiento'},
        {'index': 6, 'title': 'ACCESSORIES', 'url': 'https://www.lippioutdoor.com/collections/accesorios'},
    ]

    def request_list_by_group(self, gp: dict, pageindex: int):
        requrl = gp['url']
        if pageindex > 1:
            requrl = f"{gp['url']}?page={pageindex}"
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex={pageindex}--url:{requrl}--"
        print(logmsg)
        # mustin = ['step', 'page', 'group', 'FromKey']
        return Request(requrl, callback=self.parse_list, meta=dict(page=pageindex, step=1, gp=gp, group=gp.get('index'), FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def start_requests(self):
        for gp in self.start_urls_group:
            yield self.request_list_by_group(gp, 1)

    def parse_list(self, response: TextResponse):
        pagesize = 12
        meta = response.meta
        gp = meta['gp']
        pageindex = meta['page']
        # self.logger.debug(f"---------parse_list--pageindex={pageindex}---")
        self.lg.debug(f"-------parse_list---requrl:{response.url}--pageindex={pageindex}--")

        if 'dl' in meta:
            # print("------Skiped------parse_list---", response.url, pageindex)
            self.lg.debug(f"----Skiped------parse_list--requrl:{response.url}--pageindex:{pageindex}")
            dl = meta['dl']
            prods = dl['ProductList']
            total_count = dl['TotalCount']
        else:
            prods = []
            nds = response.xpath('//ul[@id="product-grid"]/li')

            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = gp.get('title')
                purl = self.get_text_by_path(nd, './/a[@class="full-unstyled-link"]/@href')
                if not purl or purl == "":
                    continue
                dd['Url'] = self.get_site_url(purl)
                dd['Title'] = self.get_text_by_path(nd, './/a[@class="full-unstyled-link"]/text()')
                img = self.get_text_by_path(nd, './/div[@class="card__media"]//img/@src')
                #   src="//www.lippioutdoor.com/cdn/shop/files/c6380-e02910ec-c0a6-4ca4-b422-f1c270b33443_ea16d3bd-4476-4540-aa95-48d5db968e25.jpg?v=1733205606&width=1500"
                if img and img.startswith('//www.lippioutdoor.com'):
                    img = 'https:'+img
                    dd['Image'] = img
                    dd['Thumbnail'] = img.replace('width=1500', 'width=300')
                    dd['image_urls'] = [dd['Thumbnail']]

                old_price_text = self.get_text_by_path(nd, './/div[@class="price__container"]//s[@class="price-item price-item--regular"]/text()')
                dd['OldPriceText'] = old_price_text
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None
                
                price_text = self.get_text_by_path(nd, './/div[@class="price__container"]//span[@class="price-item price-item--sale price-item--last"]/text()')
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None

                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)

            #   <span id="ProductCount">1450 productos</span>
            total_text = self.get_text_by_path(response, '//span[@id="ProductCount"]/text()')  # response.xpath('//span[@id="ProductCount"]/text()').get()
            total_count = 0
            if total_text.endswith('productos'):
                # total_count = int(re.findall(r'\d+', total_text)[0])
                total_count = int(total_text.replace('productos', '').strip())
            dl = {'TotalCount': total_count, 'PageIndex': pageindex, 'PageSize': pagesize, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST, 'ProductList': prods}
            if len(prods) == 0:
                return
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)

        for dd in prods:
            # yield dd
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            # https://www.lippioutdoor.com/products/zapatilla-hombre-vulcano-onyx-bdry-cafe-lippi.js
            yield Request(dd['Url'] + '.js', self.parse_detail, meta=dict(dd=dd, page=pageindex, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))

        if pageindex * pagesize < total_count:
            yield self.request_list_by_group(gp, pageindex+1)


    def parse_detail(self, response: TextResponse):
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:
            # result_txt = response.xpath("//pre/text()").get()
            # result = json.loads(result_txt)
            
            result = response.json()
            # price: 7699000 compare_at_price:10999000
            if not dd['OldPrice'] and result.get('compare_at_price'):
                dd['OldPrice'] = float(result.get('compare_at_price')/100)
            if not dd['FinalPrice'] and result.get('price'):
                dd['FinalPrice'] = float(result.get('price')/100)
            if not dd['OldPrice'] or dd['OldPrice'] == 0:
                dd['OldPrice'] = dd['FinalPrice']
            dd['Description'] = result.get('description')
            dd['UrlKey'] = result.get('handle')
            dd['PublishedAt'] = result.get('published_at')
            dd['Tags'] = result.get('tags')
            dd['Title'] = result.get('title')
            dd['Category'] = result.get('type')
            dd['Brand'] = result.get('vendor')
            sizelist = []
            for sz in result.get('variants'):
                sizelist.append(sz.get('title'))
            dd["SizeList"] = sizelist
            lensz = len(sizelist)
            if lensz == 0:
                lensz = 1
            dd['SizeNum'] = lensz
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            dd['DataRaw'] = response.text
            yield dd
