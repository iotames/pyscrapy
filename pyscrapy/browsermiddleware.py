from scrapy import signals
from DrissionPage import Chromium
from scrapy.http import Request, HtmlResponse


class BrowserMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    browser: Chromium
    enabled: bool = False

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def __del__(self):
        if self.enabled:
            self.browser.quit()  # 关闭浏览器
            self.enabled = False
            print("浏览器已关闭")

    def process_request(self, request, spider):
        if 'browser' in request.meta:
            if not self.enabled:
                # 连接浏览器
                self.browser = Chromium()
                self.enabled = True
                print("浏览器启动成功")
            # 获取标签页对象
            tab = self.browser.latest_tab
            if 'do_not_request' in request.meta:
                pass
            else:
                tab.get(request.url)
            if 'scroll_down' in request.meta:
                if 'scroll_times' in request.meta:
                    for i in range(0, request.meta['scroll_times']):
                        print(f"----scroll_down--{i}---")
                        tab.wait(1)
                        tab.scroll.down(request.meta['scroll_down'])
                else:
                    tab.wait(1)
                    tab.scroll.down(request.meta['scroll_down'])
            if 'wait_element' in request.meta:
                tab.ele(request.meta['wait_element']).wait.displayed()
            if 'click_element' in request.meta:
                print("点击元素：", request.meta['click_element'])
                # tab.ele('xpath://button[@class="btn btn-icon-only btn-nav"][2]').click()
                tab.ele(request.meta['click_element']).click()
            if 'scroll_down' in request.meta:
                tab.scroll.down(request.meta['scroll_down'])
            return HtmlResponse(url=request.url, body=tab.html, request=request, status=200, encoding='utf-8')

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
