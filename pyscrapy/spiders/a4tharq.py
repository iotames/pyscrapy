import scrapy


class A4tharqSpider(scrapy.Spider):
    name = "4tharq"
    allowed_domains = ["4tharq.com"]
    start_urls = ["https://4tharq.com"]

    def parse(self, response):
        pass
