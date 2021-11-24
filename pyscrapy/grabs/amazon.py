from pyscrapy.extracts.amazon import GoodsRankingList as XRankingList, GoodsDetail as XDetail, Goods as XGoods
from pyscrapy.grabs.basegrab import BaseGrab, BaseElement
from pyscrapy.items import AmazonGoodsItem


class GoodsRankingList(BaseGrab):

    @property
    def elements(self) -> list:
        return self.response.xpath(XRankingList.xpath_goods_items)


class GoodsInRankList(BaseElement):

    @property
    def url(self) -> str:
        url_ele = self.element.xpath(XRankingList.xpath_url)
        if not url_ele:
            return ''
        url = url_ele.get().strip()
        url = XGoods.get_site_url(url)
        return url

    @property
    def reviews_num(self):
        ele = self.element.xpath(XRankingList.xpath_review)
        if not ele:
            return 0
        review_text = ele.get()
        # print('===================review_text=================')
        # print(review_text)
        return int(review_text.replace(',', ''))

    @property
    def code(self):
        return XGoods.get_code_by_url(self.url)

    @property
    def item(self) -> AmazonGoodsItem:
        goods_item = AmazonGoodsItem()
        url = self.url
        image = self.element.xpath(XRankingList.xpath_goods_img).get()
        goods_item["url"] = url
        goods_item["image"] = image
        goods_item["code"] = self.code
        goods_item["title"] = self.element.xpath(XRankingList.xpath_goods_title).get()
        goods_item["reviews_num"] = self.reviews_num
        goods_item["image_urls"] = [image]
        return goods_item



