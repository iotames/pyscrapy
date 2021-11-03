# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import Request, HtmlResponse
from config import Spider as SpiderConfig, UserAgent, HttpProxy
from config import Selenium
from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class PyscrapySpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PyscrapyDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    user_agent: UserAgent
    http_proxy: HttpProxy

    def __init__(self):
        spider_config = SpiderConfig()
        self.user_agent = spider_config.get_component(UserAgent.name)
        self.http_proxy = spider_config.get_component(HttpProxy.name)

    @classmethod
    def from_crawler(cls, crawler):
        print('PyscrapyDownloaderMiddleware is starting ...')
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request: Request, spider):
        # print('PyscrapyDownloaderMiddleware  process_request is starting ...')
        settings = spider.settings
        deny_list = settings.getlist('COMPONENTS_NAME_LIST_DENY')
        if self.user_agent and (UserAgent.name not in deny_list):
            request.headers['User-Agent'] = self.user_agent.choice_one_from_items()
        if self.http_proxy and (UserAgent.name not in deny_list):
            proxy_addr = self.http_proxy.choice_one_from_items()
            splash_enabled = settings.getbool('SPLASH_ENABLED')
            if not splash_enabled:
                # request.meta['splash']['args']['proxy'] = proxy_addr 会出现本地IP代理池接口服务请求也走代理
                request.meta['proxy'] = proxy_addr

        referer = request.meta.get('referer', None)
        if referer:
            request.headers['referer'] = referer
        # print(request.headers)

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SeleniumMiddleware:

    browser = None
    enabled = False

    def __init__(self, selenium=None, enabled=False):
        self.enabled = enabled
        if enabled:
            timeout = selenium.get_config()['timeout']
            self.browser = selenium.get_driver()
            self.browser.set_page_load_timeout(timeout)

    def __del__(self):
        if self.enabled:
            self.browser.close()
            self.browser.quite()

    def process_request(self, request, spider):
        if not self.browser:
            return None
        try:
            print('SeleniumMiddleware  process_request is starting ...')
            self.browser.get(request.url)
            request.meta['browser']: WebDriver = self.browser
            return HtmlResponse(url=request.url, body=self.browser.page_source, request=request, status=200,
                                encoding='utf-8')
        except TimeoutException:
            return HtmlResponse(url=request.url, status=500, request=request)

    @classmethod
    def from_crawler(cls, crawler):
        print('SeleniumMiddleware is Starting ...')
        enabled = crawler.settings.getbool('SELENIUM_ENABLED')
        return cls(selenium=Selenium(), enabled=enabled)
