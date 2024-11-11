import scrapy


class RepresentcloSpider(scrapy.Spider):
    name = "representclo"
    allowed_domains = ["representclo.com"]
    start_urls = ["https://representclo.com"]

    def parse(self, response):
        pass
