from scrapy.http import TextResponse
from parsel.selector import SelectorList
from service import Uri
import re


class BaseGrab(object):

    spider = None

    @staticmethod
    def text_get(xpath: str, response) -> str:
        ele = response.xpath(xpath)
        if ele:
            return ele.get().strip()
        return ''

    def get_url(self, url):
        return Uri.get_url(url, self.spider.base_url)

    @staticmethod
    def get_text_by_re(pattern, text) -> str:
        ress = re.findall(pattern, text)
        if ress:
            return ress[0]
        return ''


class BaseResponse(BaseGrab):

    response: TextResponse

    def __init__(self, response: TextResponse):
        self.response = response

    def get_text(self, xpath: str) -> str:
        return self.text_get(xpath, self.response)


class BaseElement(BaseGrab):

    element: SelectorList

    def __init__(self, element: SelectorList):
        self.element = element

    def get_text(self, xpath: str) -> str:
        return self.text_get(xpath, self.element)

