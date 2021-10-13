import scrapy
from scrapy.http import TextResponse
from ..items import GympluscoffeeGoodsItem, GympluscoffeeCategoryItem
from ..helpers import Logger


class GympluscoffeeSpider(scrapy.Spider):
    name = 'gympluscoffee'
    site_id = 0
    domain = 'gympluscoffee.com'
    base_url = 'https://gympluscoffee.com'
    allowed_domains = ['gympluscoffee.com']
    start_urls = [
        'https://gympluscoffee.com/collections/merch?page=1',
        'https://gympluscoffee.com/collections/mens?page=1',
        'https://gympluscoffee.com/collections/womens?page=1'
    ]
    categories_info = {
        'merch': {'id': 0},
        'mens': {'id': 0},
        'womens': {'id': 0}
    }
    url_to_category_name_map = {
        'https://gympluscoffee.com/collections/merch': 'merch',
        'https://gympluscoffee.com/collections/mens': 'mens',
        'https://gympluscoffee.com/collections/womens': 'womens'
    }

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)
        logs_dir = ''
        if 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        self.mylogger = Logger(logs_dir)

    def parse(self, response: TextResponse):
        goods_list = response.xpath('//a[@class="product-info__caption "]')
        # page_ele = response.xpath('//div[@id="bc-sf-filter-bottom-pagination"]/span[@class="page"][last()]')
        if not goods_list:
            return False
        request_url = response.url
        self.mylogger.debug("request_url: " + request_url)
        url_info = request_url.split('?')
        current_page = int(url_info[1].split('=')[1])
        category_name = ''
        if url_info[0] in self.url_to_category_name_map:
            category_name = self.url_to_category_name_map[url_info[0]]
            category_item = GympluscoffeeCategoryItem()
            category_item['name'] = category_name
            yield category_item

        items = GympluscoffeeGoodsItem()
        for goods in goods_list:
            # href = goods.xpath('@href').extract()[0]
            href = goods.xpath('@href').get()
            title = goods.xpath('.//div/span[1]/text()').get()
            items['goods_title'] = title
            items['goods_url'] = href
            items['category_name'] = category_name
            items['category_id'] = self.categories_info[category_name]['id']
            # self.mylogger.debug('GOODS: ' + title + " : " + href)
            yield items

        next_url = url_info[0] + "?page=" + str(current_page + 1)
        # self.mylogger.debug("next_url: " + next_url)
        yield scrapy.Request(url=next_url, callback=self.parse)
        # type(response)
        # dir(response)
        # help(response)
