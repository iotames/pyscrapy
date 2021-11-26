from pyscrapy.grabs.basegrab import BaseResponse
from scrapy.http import TextResponse


class BasePage(BaseResponse):

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

