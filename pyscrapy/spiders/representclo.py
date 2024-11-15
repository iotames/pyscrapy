from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem
import json
import re


class RepresentcloSpider(BaseSpider):
    name = "representclo"
    base_url = "https://row.representclo.com"
    allowed_domains = ["representclo.com", "row.representclo.com", "sfycdn.speedsize.com"]
    start_urls = ["https://row.representclo.com/collections/discover-all-products?page=1&section_id=template--18673259839705__main"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_URI': 'representclo.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'Category', 'Title',  'Color', 'PriceText', 'FinalPrice', 'SizeList', 'SizeNum', 'Material', 'Url', 'Image']
    }

    def start_requests(self):
        for requrl in self.start_urls:
            print('------start_requests----', requrl)
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1))
    
    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        print(f"------------page={page}----", response.url)
        self.logger.debug(f"---------parse_list--page={page}---")

        # 提取商品列表
        nds = response.xpath('//ul[@id="product-grid"]/li')

        for nd in nds:
            dd = BaseProductItem()

            # 提取缩略图
            img = nd.xpath('.//img/@src').get()
            if img:
                dd['Image'] = self.get_site_url(img)
                img = img.replace('width=2000', 'width=200')
                dd['Thumbnail'] = self.get_site_url(img)
            
            # 提取商品URL  
            url = nd.xpath('.//a[@class="flex flex-col w-full group"]/@href').get()
            dd['Url'] = self.get_site_url(url)

            # 提取商品标题
            title = nd.xpath('.//h3[@class="font-global_weight text-[10px] lg:text-xs"]/text()').get()
            dd['Title'] = title.strip() if title else None

            # 提取商品颜色
            color = nd.xpath('.//span[@class="text-primary-gray"]/span[@class="font-medium capitalize"]/text()').get()
            dd['Color'] = color.strip() if color else None

            # 提取商品价格
            price_text = nd.xpath('.//span[@class="uppercase font-normal"]/text()').get()
            dd['PriceText'] = price_text.strip() if price_text else None
            dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
            
            # dd['image_urls'] = [dd['Thumbnail']]
            # yield dd
            yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd))

        # 提取下一页链接
        pagination_json_str = response.xpath('//script[@id="collection-pagination-json"]/text()').get()
        if pagination_json_str:
            pagination_json = json.loads(pagination_json_str)
            next_page_url = pagination_json.get('next', {}).get('url')
            if next_page_url:
                next_page_url = self.get_site_url(next_page_url)
                next_page_num = page + 1
                print(f"------------next_page-{next_page_num}---", next_page_url)
                yield Request(next_page_url, callback=self.parse_list, meta=dict(page=next_page_num))

    def parse_detail(self, response: TextResponse):
        meta = response.meta
        dd = meta['dd']
        # 提取 JSON 字符串
        # script_text = response.xpath('//script[@id="web-pixels-manager-setup"]/text()').get()
        script_text = response.xpath('//script[contains(text(), "var meta =")]/text()').get()
        if script_text:
            # json_match = re.search(r'var meta = ({.*?});', script_text, re.DOTALL)
            json_match = re.search(r'var meta = (\{.*?\});', script_text, re.DOTALL)

            # print('=====parse_detail--=script_text====json_match==', json_match, script_text)
            if json_match:
                meta_json_str = json_match.group(1)
                try:
                    meta_data = json.loads(meta_json_str)
                    dd['Category'] = meta_data['product'].get('type')
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON data: {e}")

        # 提取商品尺寸列表
        size_list = response.xpath('//form[@class="form product-form w-full"]//select/option/text()').getall()
        dd['SizeList'] = [size.strip() for size in size_list if size.strip()]
        dd['SizeNum'] = len(dd['SizeList'])

        # 提取商品材质
        material = response.xpath('//div[@id="product_description"]//p[contains(text(), "Composition:")]/text()').get()
        if material:
            material = material.replace("Composition: ", "").strip()
        dd['Material'] = material
        yield dd

    def get_price_by_text(self, price_text):
        if price_text:
            price = re.search(r'\$([\d,]+)', price_text)
            if price:
                return float(price.group(1).replace(',', ''))
        return None

    def get_site_url(self, url):
        if url and not url.startswith('http'):
            return self.base_url + url
        return url
