from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage


class NoseridersurfSpider(BaseSpider):
    name = "noseridersurf"
    base_url = "https://noseridersurf.com"
    allowed_domains = ["noseridersurf.com"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'PublishedAt', 'Title', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'noseridersurf.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 1, 'title': 'Cropped Rash Guards', 'url': 'https://noseridersurf.com/collections/cropped-rash-guard'},
        {'index': 2, 'title': 'Retro Surf Suits', 'url': 'https://noseridersurf.com/collections/retro-surf-suits'},
        {'index': 3, 'title': 'Surf Bikinis', 'url': 'https://noseridersurf.com/collections/surf-bikinis'},
        {'index': 4, 'title': 'Bikini Tops', 'url': 'https://noseridersurf.com/collections/bikini-tops'},
        {'index': 5, 'title': 'Bikini Bottoms', 'url': 'https://noseridersurf.com/collections/bikini-bottoms'},
        {'index': 6, 'title': 'Surf Shorts', 'url': 'https://noseridersurf.com/collections/surf-shorts-women'},
        {'index': 7, 'title': 'Surf Leggings', 'url': 'https://noseridersurf.com/collections/surf-leggings'},
        {'index': 8, 'title': 'long sleeve surf suits', 'url': 'https://noseridersurf.com/collections/long-sleeve-surf-suits'},
        {'index': 9, 'title': 'Modest Swimwear', 'url': 'https://noseridersurf.com/collections/modest-swimwear'},
        {'index': 10, 'title': 'Overswim', 'url': 'https://noseridersurf.com/collections/overswim'},
        {'index': 11, 'title': 'Jumpers', 'url': 'https://noseridersurf.com/collections/jumpers'},
        {'index': 12, 'title': 'Corduroy Totes', 'url': 'https://noseridersurf.com/collections/corduroy-tote-bags'},
        {'index': 13, 'title': 'Shop Sale', 'url': 'https://noseridersurf.com/collections/sale'},
        {'index': 14, 'title': 'All', 'url': 'https://noseridersurf.com/collections/all'},
    ]
    
    # start_urls = []
    
    def start_requests(self):
        self.pageSize = 11
        for gp in self.start_urls_group:
            requrl = gp['url']
            groupName = gp['title']
            groupIndex = gp['index']
            print('------start_requests----', groupIndex, groupName, requrl)
            yield Request(requrl, callback=self.parse_list, meta=dict(page=1, step=1, group=groupIndex, GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))            

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        groupName = meta['GroupName']
        self.lg.debug(f"-------parse_list---requrl:{response.url}--page={page}--")

        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            prods = []
            # 1. 获取当前页所有商品
            nds = response.xpath('//ul[@id="product-grid"]/li')
            for nd in nds:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                
                url = nd.xpath('.//a[@class="product-card-title"]/@href').get()
                dd['Url'] = self.get_site_url(url)
                
                title = nd.xpath('.//a[@class="product-card-title"]/text()').get()
                dd['Title'] = title.strip() if title else None
                
                old_price_text = nd.xpath('.//span[@class="price"]/del/span/text()').get()
                dd['OldPriceText'] = old_price_text.strip() if old_price_text else None
                dd['OldPrice'] = self.get_price_by_text(dd['OldPriceText']) if dd['OldPriceText'] else None
                
                price_text = nd.xpath('.//span[@class="price"]/ins/span/text()').get()
                dd['PriceText'] = price_text.strip() if price_text else None
                dd['FinalPrice'] = self.get_price_by_text(dd['PriceText']) if dd['PriceText'] else None
                
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            nextPageUrl = ""
            next_page = response.xpath('//ul[@class="page-numbers nav-links"]/li[@class="next"]/a/@href').get()
            if next_page:
                nextPageUrl = self.get_site_url(next_page)
            dl = {'ProductList': prods, 'NextPageUrl': nextPageUrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            yield Request(dd['Url'] + ".js", self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        
        if dl['NextPageUrl'] != "":
            print(f"------------next_page-{dl['NextPageUrl']}---")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=dict(page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    def parse_detail(self, response: TextResponse):
        # {"id":7798067298536,"title":"Classic Long-Sleeve Surf Suit in Espresso Brown","handle":"long-sleeve-surf-suit-brown","description":"\u003cp\u003eOur Classic Long Sleeve Noserider Surf Suit is a sleek, backless one-piece designed for both style and performance. With a flattering scooped neckline and a bold back cutout, this suit offers a perfect blend of elegance and function. Designed to feel like a second skin, this surf suit enhances your natural shape, ensuring you feel confident and comfortable in and out of the water. More than just stylish, it\u2019s engineered for performance, making it an ideal choice for surfers of all skill levels. Crafted with double lining and strong elastic support, it provides a secure fit, whether you're catching waves or lounging by the shore.\u003c\/p\u003e\n\u003cp\u003e\u003cstrong\u003eDetails:\u003c\/strong\u003e\u003c\/p\u003e\n\u003cul\u003e\n\u003cli\u003e3\/4 length sleeve design for added coverage\u003c\/li\u003e\n\u003cli\u003eScooped neckline with a striking back cutout\u003c\/li\u003e\n\u003cli\u003eDesigned to feel like a second skin, enhancing your natural shape\u003c\/li\u003e\n\u003cli\u003eDouble-lined for premium comfort\u003c\/li\u003e\n\u003cli\u003eHigh waisted to enhance your silhouette\u003c\/li\u003e\n\u003cli\u003eStrong elastic support for a secure fit\u003c\/li\u003e\n\u003cli\u003eEco-friendly material made from recycled plastic\u003c\/li\u003e\n\u003cli\u003eQuick-drying fabric with UV protection\u003c\/li\u003e\n\u003c\/ul\u003e\n\u003c!----\u003e","published_at":"2022-08-04T14:16:53+08:00","created_at":"2022-05-27T16:05:26+08:00","vendor":"noseridersurf","type":"","tags":["brown","full coverage surf suits","long sleeve","modest swimwear","one piece surf suits","one piece swimwear","one-piece","summer collection"],"price":16000,"price_min":16000,"price_max":16000,"available":true,"price_varies":false,"compare_at_price":null,"compare_at_price_min":0,"compare_at_price_max":0,"compare_at_price_varies":false,"variants":[{"id":45262118879464,"title":"xx-small","option1":"xx-small","option2":null,"option3":null,"sku":"LS-ESP-XXS-504","requires_shipping":true,"taxable":true,"featured_image":null,"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - xx-small","public_title":"xx-small","options":["xx-small"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"requires_selling_plan":false,"selling_plan_allocations":[]},{"id":43210624336104,"title":"x-small","option1":"x-small","option2":null,"option3":null,"sku":"LS-ESP-XS-504","requires_shipping":true,"taxable":true,"featured_image":{"id":38854280347880,"product_id":7798067298536,"position":5,"created_at":"2022-08-02T12:42:42+08:00","updated_at":"2023-01-19T22:54:23+08:00","alt":null,"width":3648,"height":5472,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","variant_ids":[43210624336104,43210624401640,43210624467176,43210624532712,43210624565480]},"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - x-small","public_title":"x-small","options":["x-small"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"featured_media":{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"}},"requires_selling_plan":false,"selling_plan_allocations":[]},{"id":43210624401640,"title":"small","option1":"small","option2":null,"option3":null,"sku":"LS-ESP-S-504","requires_shipping":true,"taxable":true,"featured_image":{"id":38854280347880,"product_id":7798067298536,"position":5,"created_at":"2022-08-02T12:42:42+08:00","updated_at":"2023-01-19T22:54:23+08:00","alt":null,"width":3648,"height":5472,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","variant_ids":[43210624336104,43210624401640,43210624467176,43210624532712,43210624565480]},"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - small","public_title":"small","options":["small"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"featured_media":{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"}},"requires_selling_plan":false,"selling_plan_allocations":[]},{"id":43210624467176,"title":"medium","option1":"medium","option2":null,"option3":null,"sku":"LS-ESP-M-504","requires_shipping":true,"taxable":true,"featured_image":{"id":38854280347880,"product_id":7798067298536,"position":5,"created_at":"2022-08-02T12:42:42+08:00","updated_at":"2023-01-19T22:54:23+08:00","alt":null,"width":3648,"height":5472,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","variant_ids":[43210624336104,43210624401640,43210624467176,43210624532712,43210624565480]},"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - medium","public_title":"medium","options":["medium"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"featured_media":{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"}},"requires_selling_plan":false,"selling_plan_allocations":[]},{"id":43210624532712,"title":"large","option1":"large","option2":null,"option3":null,"sku":"LS-ESP-L-504","requires_shipping":true,"taxable":true,"featured_image":{"id":38854280347880,"product_id":7798067298536,"position":5,"created_at":"2022-08-02T12:42:42+08:00","updated_at":"2023-01-19T22:54:23+08:00","alt":null,"width":3648,"height":5472,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","variant_ids":[43210624336104,43210624401640,43210624467176,43210624532712,43210624565480]},"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - large","public_title":"large","options":["large"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"featured_media":{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"}},"requires_selling_plan":false,"selling_plan_allocations":[]},{"id":43210624565480,"title":"x-large","option1":"x-large","option2":null,"option3":null,"sku":"LS-ESP-XL-504","requires_shipping":true,"taxable":true,"featured_image":{"id":38854280347880,"product_id":7798067298536,"position":5,"created_at":"2022-08-02T12:42:42+08:00","updated_at":"2023-01-19T22:54:23+08:00","alt":null,"width":3648,"height":5472,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","variant_ids":[43210624336104,43210624401640,43210624467176,43210624532712,43210624565480]},"available":true,"name":"Classic Long-Sleeve Surf Suit in Espresso Brown - x-large","public_title":"x-large","options":["x-large"],"price":16000,"weight":500,"compare_at_price":null,"inventory_management":"shopify","barcode":null,"featured_media":{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"}},"requires_selling_plan":false,"selling_plan_allocations":[]}],"images":["\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A6994.jpg?v=1674140063","\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/Emma8414.jpg?v=1674140063","\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/IMG_3259.jpg?v=1674140063","\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7176.jpg?v=1674140063","\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7104.jpg?v=1674140063"],"featured_image":"\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A6994.jpg?v=1674140063","options":[{"name":"Size","position":1,"values":["xx-small","x-small","small","medium","large","x-large"]}],"url":"\/products\/long-sleeve-surf-suit-brown","media":[{"alt":null,"id":31426584346856,"position":1,"preview_image":{"aspect_ratio":0.667,"height":5015,"width":3343,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A6994.jpg?v=1674140063"},"aspect_ratio":0.667,"height":5015,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A6994.jpg?v=1674140063","width":3343},{"alt":null,"id":31444632535272,"position":2,"preview_image":{"aspect_ratio":0.667,"height":3590,"width":2394,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/Emma8414.jpg?v=1674140063"},"aspect_ratio":0.667,"height":3590,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/Emma8414.jpg?v=1674140063","width":2394},{"alt":null,"id":31444639580392,"position":3,"preview_image":{"aspect_ratio":0.667,"height":4219,"width":2813,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/IMG_3259.jpg?v=1674140063"},"aspect_ratio":0.667,"height":4219,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/IMG_3259.jpg?v=1674140063","width":2813},{"alt":null,"id":31426584281320,"position":4,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7176.jpg?v=1674140063"},"aspect_ratio":0.667,"height":5472,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7176.jpg?v=1674140063","width":3648},{"alt":null,"id":31426584314088,"position":5,"preview_image":{"aspect_ratio":0.667,"height":5472,"width":3648,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063"},"aspect_ratio":0.667,"height":5472,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7068.jpg?v=1674140063","width":3648},{"alt":null,"id":31426584248552,"position":6,"preview_image":{"aspect_ratio":0.667,"height":5180,"width":3453,"src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7104.jpg?v=1674140063"},"aspect_ratio":0.667,"height":5180,"media_type":"image","src":"https:\/\/cdn.shopify.com\/s\/files\/1\/0627\/2162\/2248\/products\/3A4A7104.jpg?v=1674140063","width":3453}],"requires_selling_plan":false,"selling_plan_groups":[]}            
        meta = response.meta
        dd = meta['dd']
        if 'SkipRequest' in dd:
            # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
            yield dd
        else:
            dd['DataRaw'] = response.text
            data = response.json()
            dd['Title'] = data['title']
            dd['PublishedAt'] = data['published_at']
            dd['Description'] = data['description']
            dd['Tags'] = data['tags']
            dd['Image'] = self.get_site_url(data['featured_image'])
            dd['Thumbnail'] = dd['Image'] + "&w=300"
            szs = []
            for vv in data['variants']:
                szs.append(vv['title'])
            dd['SizeList'] = szs
            dd['SizeNum'] = len(szs)
            dd['FinalPrice'] = float(data['price']/100)
            if data['compare_at_price']:
                dd['OldPrice'] = float(data['compare_at_price']/100)
            else:
                dd['OldPrice'] = dd['FinalPrice']
            dd['image_urls'] = [dd['Thumbnail']]
            self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
            yield dd


