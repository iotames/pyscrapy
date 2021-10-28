from scrapy.http import TextResponse, request
from .basespider import BaseSpider
from selenium.webdriver.remote.webdriver import WebDriver
from scrapy import Request


class HelloSpider(BaseSpider):
    name: str = 'hello'

    custom_settings = {
        'SELENIUM_ENABLED': True
    }

    def __init__(self, name=None, **kwargs):
        super(HelloSpider, self).__init__(name=name, **kwargs)
        self.allowed_domains = ['httpbin.org', 'baidu.com']
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
        print('current url =======================' + url)
        if url.find('httpbin') > -1:
            self.mylogger.debug(text)
        browser: WebDriver = response.meta['browser']
        if url.find('baidu.com') > -1:
            browser.find_element_by_xpath('//*[@id="kw"]').send_keys('hello word')
            browser.find_element_by_xpath('//*[@id="su"]').click()
        # browser.get('https://www.baidu.com')
        yield Request(url='https://www.baidu.com')
        # self.logger.debug(text)
