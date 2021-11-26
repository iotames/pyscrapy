from scrapy.http import TextResponse
from parsel.selector import SelectorList


class BaseGrab(object):

    @staticmethod
    def text_get(xpath: str, response) -> str:
        ele = response.xpath(xpath)
        if ele:
            return ele.get().strip()
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

