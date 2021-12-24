from scrapy.http import TextResponse, request
from .basespider import BaseSpider
from selenium.webdriver.remote.webdriver import WebDriver
from scrapy import Request
from scrapy_splash import SplashRequest
from pyscrapy.items import HelloItem
from config import Spider, HttpProxy


class HelloSpider(BaseSpider):
    name: str = 'hello'
    http_proxy: HttpProxy

    custom_settings = {
        'LOG_LEVEL': 'WARNING',  # 没有效果
        'SPLASH_URL': 'http://127.0.0.1:8050',
        'DOWNLOADER_MIDDLEWARES': {
            'pyscrapy.middlewares.PyscrapyDownloaderMiddleware': 543,
            'pyscrapy.middlewares.SeleniumMiddleware': 550,
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage'
    }

    def __init__(self, name=None, **kwargs):
        super(HelloSpider, self).__init__(name=name, **kwargs)
        self.allowed_domains = ['httpbin.org', 'baidu.com']
        self.start_urls = [
            # "https://www.google.com",
            # "https://www.baidu.com",
            "https://httpbin.org/get"
        ]
        # 初始化IP代理池
        spider_config = Spider()
        self.http_proxy = spider_config.get_component(HttpProxy.name)
        self.SELENIUM_ENABLED = True

    def start_requests(self):
        # headers = {
        #     'content-type': 'application/json',
        # }
        start_url = self.start_urls[0]
        if self.SPLASH_ENABLED:
            args = {}
            # TODO 更换UA请求头要通过splash LUA脚本注入才有效
            if self.http_proxy:
                http_proxy = self.http_proxy.choice_one_from_items()  # 从IP代理池选择一个IP代理
                print(http_proxy)
                args["proxy"] = http_proxy
            yield SplashRequest(start_url, self.parse, args=args)
        else:
            yield request.Request(
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
            self.mylogger.debug(text)
        if self.SELENIUM_ENABLED:
            yield self.parse_selenium(response)
        if self.SPLASH_ENABLED:
            yield self.parse_splash(response)
        # self.logger.debug(text)

    def parse_selenium(self, response: TextResponse):
        browser: WebDriver = response.meta['browser']
        if response.url.find('baidu.com') > -1:
            browser.find_element_by_xpath('//*[@id="kw"]').send_keys('hello word')
            browser.find_element_by_xpath('//*[@id="su"]').click()
        # browser.get('https://www.baidu.com')
        return Request(url='https://www.baidu.com')

    lua_source = """
    function main(splash, args)
        function focus(sel)
            splash:select(sel):focus()
        end
        assert(splash:go(args.url))
        assert(splash:wait(0.5))
        focus('input[name=wd]')
        splash:send_text(args.keyword)
        assert(splash:wait(0))
        splash:select('input[type=submit]'):mouse_click()
        assert(splash:wait(2))
        return splash:html()
    end
    """

    def parse_splash(self, response: TextResponse):
        # self.mylogger.debug('========parse_splash============')
        if response.url.find('baidu.com') > -1:
            return SplashRequest('https://www.baidu.com', callback=self.parse_baidu, endpoint='execute', args={
                'lua_source': self.lua_source,
                'keyword': 'hello my splash'
            })
        else:
            return SplashRequest(url='https://www.baidu.com', callback=self.parse_splash)

    def parse_baidu(self, response: TextResponse):
        self.mylogger.debug('========parse_baidu============')
        print(response.meta)  # {'splash': {'endpoint': 'execute', ...
        # print(response.text)
        self.mylogger.echo_msg = False
        self.mylogger.debug(response.text)
        item = HelloItem()
        item['image_urls'] = ['http://localhost:8050/render.png?url=https%3A%2F%2Fwww.baidu.com%2Fs%3Fwd%3Dhello%2520splash&timeout=10']
        yield item
