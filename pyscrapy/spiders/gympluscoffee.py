import scrapy


class GympluscoffeeSpider(scrapy.Spider):
    name = 'gympluscoffee'
    allowed_domains = ['gympluscoffee.com']
    start_urls = ['http://gympluscoffee.com/']

    def parse(self, response):
        pass
