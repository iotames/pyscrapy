import scrapy
from scrapy.http import TextResponse
from ..items import GympluscoffeeItem
from ..helpers import Logger


class GympluscoffeeSpider(scrapy.Spider):
    name = 'gympluscoffee'
    allowed_domains = ['gympluscoffee.com']
    start_urls = [
        'https://gympluscoffee.com/collections/merch?page=1',
        'https://gympluscoffee.com/collections/mens?page=1',
        'https://gympluscoffee.com/collections/womens?page=1'
    ]
    # page = 1
    # spider_state = {
    #     "https://gympluscoffee.com/collections/merch": True,
    #     'https://gympluscoffee.com/collections/mens': True,
    #     'https://gympluscoffee.com/collections/womens': True
    # }

    def __init__(self, name=None, **kwargs):
        super(GympluscoffeeSpider, self).__init__(name=name, **kwargs)
        self.mylogger = Logger(kwargs['logs_dir'])

    def parse(self, response: TextResponse):
        goods_list = response.xpath('//a[@class="product-info__caption "]')
        # page_ele = response.xpath('//div[@id="bc-sf-filter-bottom-pagination"]/span[@class="page"][last()]')
        if not goods_list:
            return False
        request_url = response.url
        self.mylogger.debug("request_url: " + request_url)
        url_info = request_url.split('?')
        current_page = int(url_info[1].split('=')[1])

        items = GympluscoffeeItem()
        for goods in goods_list:
            # href = goods.xpath('@href').extract()[0]
            href = goods.xpath('@href').get()
            title = goods.xpath('.//div/span[1]/text()').get()
            items['goods_title'] = title
            items['goods_url'] = href
            # self.mylogger.debug('GOODS: ' + title + " : " + href)
            yield items

        next_url = url_info[0] + "?page=" + str(current_page + 1)
        # self.mylogger.debug("next_url: " + next_url)
        yield scrapy.Request(url=next_url, callback=self.parse)
        # type(response)
        # dir(response)
        # help(response)
