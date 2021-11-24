from scrapy.http import TextResponse
from parsel.selector import SelectorList


class BaseGrab(object):

    response: TextResponse

    def __init__(self, response: TextResponse):
        self.response = response


class BaseElement(object):

    element: SelectorList

    def __init__(self, element: SelectorList):
        self.element = element

