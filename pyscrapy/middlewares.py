# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from service import Config
from scrapy import signals
from urllib.parse import quote

conf = Config.get_instance()


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

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

        # 走splash请求。仅支持GET
        splash_process = self.process_splash_request(request, spider)
        if splash_process is not None:
            return splash_process

        # 走普通请求
        proxy = conf.get_http_proxy()
        if proxy != "":
            print(f"----process_request--UsingProxy({proxy})---url({request.url})--mata({request.meta})")
            request.meta["proxy"] = proxy
        return None

    # 仅支持GET请求
    def process_splash_request(self, request, spider):
        splash_url = spider.settings.get("SPLASH_URL", "")
        user_agent = spider.settings.get("USER_AGENT", "")
        http_proxy = conf.get_http_proxy()
        port_split = http_proxy.split(":")
        proxy_port = port_split[-1]
        print(f"------process_request--UsingSplash({splash_url})--proxy_port({proxy_port})--")
        if splash_url == "" or 'splash' not in request.meta:
            return None
        lua_source_fmt = """
        splash:set_user_agent("{}")
        assert(splash:go("{}"))
        assert(splash:wait(1.5))
        return splash:html()
        """
        lua_source = lua_source_fmt.format(user_agent, request.url)
        if proxy_port != "":
            lua_source_fmt = """
            splash:on_request(function(request)
                request:set_proxy{{"0.0.0.0",{}}}
            end)
            splash:set_user_agent("{}")
            assert(splash:go("{}"))
            assert(splash:wait(1.5))
            return splash:html()
            """
            lua_source = lua_source_fmt.format(proxy_port, user_agent, request.url)
        print(f"-------process_splash_request---lua_source({lua_source})")
        q = quote(lua_source)
        reqobj = request.replace(url=f"{splash_url}/run?lua_source={q}")
        if 'proxy' in reqobj.meta:
            del reqobj.meta['proxy']
        if 'splash' in reqobj.meta:
            # 防止出现死循环
            del reqobj.meta['splash']
        return reqobj

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
