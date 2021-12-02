from pyscrapy.grabs.basegrab import BaseResponse
from scrapy.http import TextResponse


class BasePage(BaseResponse):

    @staticmethod
    def get_price_by_text(text):
        price = 0
        if text:
            info = text.split('$')  # 中文页面US$, 英文页面单位$
            if len(info) > 1:
                price = info[1]
        return price

    @staticmethod
    def check_robot_happened(response: TextResponse):
        xpath_form = '//div[@class="a-box-inner a-padding-extra-large"]/form/div[1]/div/div/h4/text()'
        ele = response.xpath(xpath_form)  # Type the characters you see in this image:
        # print(ele)  # []
        if ele:
            print('======ERROR!=======check_robot_happened==========================')
            # TODO 切换IP继续爬
            # raise RuntimeError("===============check_robot_happened=======================")
            return True
        return False

