from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request, Selector
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from utils.strfind import get_material
from urllib.parse import quote
import os
from utils.os import save_file


class GymbeamSpider(BaseSpider):

    name = "gymbeam"
    base_url = "https://gymbeam.com"
    allowed_domains = ["gymbeam.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.6,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        # 取消 URL 长度限制
        'URLLENGTH_LIMIT': None,
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'Code', 'GroupName', 'Brand', 'Category', 'MadeIn',
                               'Title', 'Color', 'PriceText', 'FinalPrice','TotalReviews',
                               'Material', 'Image', 'Url'
        ],
        # 'FEED_EXPORT_FIELDS_DICT': {"Category": "小类"}
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'gymbeam.xlsx',
        # 'FEED_FORMAT': 'xlsx'
        }

    start_urls_group = [
        {'index': 1, 'title': 'Sportswear', 'name':'clothing', 'url': 'https://gymbeam.com/clothing'}, # 39
    ]
    # start_urls = []

    def request_list_by_group(self, gp: dict, pageindex: int):
        group_name = gp.get('name')
        groupIndex = gp.get('index')
        requrl = "https://gymbeam.com/{}?p={}&is_scroll=1".format(group_name, pageindex)
        # if pageindex == 1:
        #     requrl = gp.get('url')
        referer_page = pageindex - 2
        referer = gp.get('url')
        if referer_page > 1:
            referer = "{}?p={}".format(gp.get('url'), referer_page)
        logmsg = f"----request_list_by_group--group({gp['title']})--pageindex({pageindex})--url:{requrl}--"
        print(logmsg)
        meta = dict(gp=gp, page=pageindex, step=1, group=groupIndex, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST)
        hdr = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        return Request(requrl, callback=self.parse_list, meta=meta, headers=hdr)

    def start_requests(self):
        self.page_size = 36
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
            categoryProducts = result.get('categoryProducts')
            if categoryProducts is None:
                raise ValueError("categoryProducts is empty")
            # filename = "runtime/{}.json".format(self.name)
            # save_file(filename, categoryProducts)

            total_count = result.get('productsAmount', {}).get('total', 0)
            page_index = page
            has_next_page = self.check_next_page(page_index, total_count)
            dl = {'Url': gp.get('url'), 'TotalCount': total_count, 'PageIndex': page, 'PageSize': self.page_size, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}

            # 将HTML字符串转换为Selector对象
            html_selector = Selector(text=categoryProducts)
            # 使用XPath提取产品列表
            prod_nds = html_selector.xpath('//li[@class="item product product-item"]')
            if len(prod_nds) == 0:
                raise ValueError("products is empty")
            prods = []
            for nd in prod_nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['PageIndex'] = page_index
                dd['Url'] = self.get_text_by_path(nd, './/a[@class="product-item-link"]/@href')
                if dd['Url'] is None:
                    continue
                dd['Title'] = self.get_text_by_path(nd, './/a[@class="product-item-link"]/text()')
                dd['Brand'] = self.get_text_by_path(nd, './/input[@name="gtm_product_brand"]/@value')
                dd['Code'] = self.get_text_by_path(nd, './/form[@data-role="tocart-form"]/@data-product-sku')

                # 获取缩略图
                thumbnail = self.get_text_by_path(nd, './/img[@class="lozad product-image-photo"]/@data-src')
                dd['Thumbnail'] = thumbnail
                dd['Image'] = thumbnail
                dd['image_urls'] = [thumbnail]

                # 获取评论数
                total_reviews = 0
                review_text = self.get_text_by_path(nd, './/div[@class="reviews-actions"]/a/text()')
                dd['TotalReviewsText'] = review_text
                if review_text is not None:
                    total_reviews = int(review_text.strip().strip('()').replace(' ', '').replace(',', ''))
                dd['TotalReviews'] = total_reviews

                # 获取销售价
                finalPrice = 0.0
                price_text = self.get_text_by_path(nd, './/span[@class="price"]/text()')
                if price_text:
                    dd['PriceText'] = price_text
                    finalPrice = float(self.get_text_by_path(nd, './/span[@data-price-type="finalPrice"]/@data-price-amount'))
                dd['FinalPrice'] = finalPrice
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
                #   <div data-test="pdp-product-price" class="flex gap-4 items-center"><span
                #                                 class="text-secondary text-lg font-bold leading-none"><span
                #                                     data-test="hp-bestsellers-price">€10.50</span></span></div>
            if dd['FinalPrice'] == 0:
                price_text = self.get_text_by_path(response, './/div[@data-test="pdp-product-price"]//span[@data-test="hp-bestsellers-price"]/text()')
                if price_text is not None:
                    dd['FinalPrice'] = float(price_text.replace('€', '').replace(',', ''))
                    dd['PriceText'] = price_text
            dd['Category'] = self.get_prod_attr('Main category', response)
            dd['MadeIn'] = self.get_prod_attr('Made in', response)
            dd['Color'] = self.get_prod_attr('Color', response)

            # 提取面料信息
            material_h2 = response.xpath('//div[@id="product-tabs-description"]//h2[contains(text(), "Material")]')
            if material_h2:
                material_p = material_h2.xpath('./following-sibling::p[1]/text()').get()
                if material_p:
                    dd['Material'] = material_p.strip()
            # self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}--desc({dd['Description']})--")
            yield dd
    
    def get_prod_attr(self, attr_name: str, nd):
        # <tr>
        #     <th
        #         class="hidden sm:table-cell text-left align-top leading-6 md:leading-8 md:w-1/2 md:p-0 ">
        #         Main category</th>
        #     <td data-th="Main category"
        #         class="flex justify-between align-top sm:table-cell sm:text-right md:text-left leading-6 md:leading-8 border-0 pb-4 pt-0 px-0 md:p-0 md:pl-2.5">
        #         <span class="font-bold pr-2 sm:hidden">Main category<!-- -->:</span>
        #         <div class="inline-block text-right md:text-left"><span><a title="" aria-label=""
        #                     href="https://gymbeam.com/mens-t-shirts"
        #                     class="block text-secondary hover:text-secondary-hover">Men&#x27;s
        #                     T-Shirts</a></span></div>
        #     </td>
        # </tr>
        # <tr>
        #     <th
        #         class="hidden sm:table-cell text-left align-top leading-6 md:leading-8 md:w-1/2 md:p-0 ">
        #         Top</th>
        #     <td data-th="Top"
        #         class="flex justify-between align-top sm:table-cell sm:text-right md:text-left leading-6 md:leading-8 border-0 pb-4 pt-0 px-0 md:p-0 md:pl-2.5">
        #         <span class="font-bold pr-2 sm:hidden">Top<!-- -->:</span>
        #         <div class="inline-block text-right md:text-left"><span><span>short
        #                     sleeve</span></span></div>
        #     </td>
        # </tr>
        val = self.get_text_by_path(nd, '//td[@data-th="{}"]/div/span/span/text()'.format(attr_name))
        if val is None:
            val = self.get_text_by_path(nd, '//td[@data-th="{}"]/div/span/a/text()'.format(attr_name))
        return val
