from scrapy.http import TextResponse, request
from .basespider import BaseSpider


class HelloSpider(BaseSpider):
    name: str = 'hello'

    def __init__(self, name=None, **kwargs):
        super(HelloSpider, self).__init__(name=name, **kwargs)
        self.start_urls = [
            # "https://www.google.com",
            # "https://www.baidu.com",
            "https://httpbin.org/get"
        ]

    def start_requests(self):
        # headers = {
        #     'content-type': 'application/json',
        # }
        for url in self.start_urls:
            yield request.Request(
                url,
                callback=self.parse,
                # method='POST',
                # headers=headers
            )

    def parse(self, response: TextResponse, **kwargs):
        text = response.text
        url = response.url
        print(url)
        if url.find('httpbin') > -1:
            self.mylogger.debug(text)
        # self.logger.debug(text)
