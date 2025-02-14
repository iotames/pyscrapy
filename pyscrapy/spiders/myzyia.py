from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material


class MyzyiaSpider(BaseSpider):
    name = "myzyia"
    base_url = "https://myzyia.com"
    allowed_domains = ["myzyia.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 8,  # default 8
        'CONCURRENT_REQUESTS': 8,  # default 16 recommend 5-8

        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Category', 'Title', 'PriceText', 'FinalPrice', 'OldPrice', 'Material', 'Url']
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'myzyia.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': "Women", 'name':'women', 'code': '', 'url': 'https://new.myzyia.com/CORPORATE/en_CA/women.html'}, # 1175 products
        {'index': 2, 'title': "Men", 'name':'men', 'code': '', 'url': 'https://new.myzyia.com/CORPORATE/en_CA/men.html'}, # 651 products
        {'index': 3, 'title': "Kids", 'name':'kids-juniors', 'code': '', 'url': 'https://new.myzyia.com/CORPORATE/en_CA/kids-juniors.html'}, # 188 products
        {'index': 4, 'title': "Accessories", 'name':'accessories', 'code': '', 'url': 'https://new.myzyia.com/CORPORATE/en_CA/accessories.html'}, # 115 products
    ]

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        groupIndex = gp.get('index')
        requrl = "https://new.myzyia.com/CORPORATE/en_CA/{}.html?p={}&product_list_limit=36".format(group_name, pageindex, self.page_size)
        referer = "https://new.myzyia.com/CORPORATE/en_CA/{}.html?p={}&product_list_limit=36".format(group_name, pageindex-1, self.page_size)
        if pageindex == 1:
            requrl = "https://new.myzyia.com/CORPORATE/en_CA/{}.html?product_list_limit={}".format(group_name, self.page_size)
            referer = "https://new.myzyia.com/CORPORATE/en_CA/{}.html?p={}&product_list_limit=36".format(group_name, 2, self.page_size)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'referer': referer,
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 36
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
            total_count = dl['TotalCount']
            page_index = dl['PageIndex']
            has_next_page = self.check_next_page(page, total_count)
        else:
            # 提取商品列表
            totalstr = self.get_text_by_path(response, '//span[@class="toolbar-number"]/text()')
            total_count = int(totalstr.replace(',', ''))
            nds = response.xpath('//li[@class="item product product-item"]')
            has_next_page = self.check_next_page(page, total_count)

            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
   
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
                img = self.get_text_by_path(nd, './/img[@class="product-image-photo"]/@src')
                if img is not None:
                    dd['Thumbnail'] = img

                # 提取商品URL  
                dd['Url'] = self.get_text_by_path(nd, './/a[@class="product-item-link"]/@href')
                dd['Title'] = self.get_text_by_path(nd, './/a[@class="product-item-link"]/text()')

                # 价格提取部分
                dd['PriceText'] = self.get_text_by_path(nd, './/span[@data-price-type="finalPrice"]/span/text()')
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                dd['OldPriceText'] = self.get_text_by_path(nd, './/span[@data-price-type="oldPrice"]/span/text()')
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None

                code = self.get_text_by_path(nd, './/div[@class="product sku product-item-sku"]/text()')
                # Item #4430
                dd['Code'] = code.replace('Item #', '') if code else None

                print(f"----code({dd['Code']})--sale_price_text({dd['PriceText']})---FinalPrice({dd['FinalPrice']})---old_price_text({dd['OldPriceText']})--old_price({dd['OldPrice']})---")

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
            desnds = response.xpath('//div[@class="product attribute description"]//ul/li/text()')
            if desnds is not None:
                for desnd in desnds.getall():
                    # print(f"--------purl({dd['Url']})-------desnd({desnd})---")
                    if desnd.find("%") >= 0:
                        mtlist = get_material(desnd)
                        if len(mtlist) > 0:
                            dd['Material'] = ";".join(mtlist)
                            break
            # sznds = response.xpath('//div[@class="block-swatch-list"]//label/text()')
            # if sznds is not None:
            #     szlist = sznds.getall()
            #     szlist111 = []
            #     for sz in szlist:
            #         szlist111.append(sz.strip())
            #     dd['SizeList'] = szlist111
            #     dd['SizeNum'] = len(szlist111)
            yield dd

    def check_next_page(self, page_index, total_count):
        return page_index * self.page_size < total_count