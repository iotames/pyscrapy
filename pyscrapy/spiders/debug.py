from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request


class DebugSpider(BaseSpider):
    name: str = 'debug'

    custom_settings = {
        # 'DOWNLOAD_DELAY': 1,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3, # default 8
        'CONCURRENT_REQUESTS': 6, # default 16 recommend 5-8
    }

    def __init__(self, name=None, **kwargs):
        self.allowed_domains = ['httpbin.org', 'baidu.com']
        self.base_url = "https://httpbin.org"
        self.domain = "httpbin.org"
        super(DebugSpider, self).__init__(name=name, **kwargs)

    def start_requests(self):
        start_url = "https://httpbin.org/get"
        yield Request(
            start_url,
            callback=self.parse,
            # method='POST',
            # headers=headers
        )

    def parse(self, response: TextResponse, **kwargs):
        text = response.text
        url = response.url
        print('current url =======================' + url)
        if url.find('httpbin') > -1:
            print(text)
