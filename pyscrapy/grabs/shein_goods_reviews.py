from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.extracts.shein import GoodsDetail as XDetail, Common as XShein
from pyscrapy.grabs.amazon import BasePage
from pyscrapy.items import BaseGoodsItem
from urllib.parse import urlencode


class ReviewRequest(object):
    """
    大概每销售50-100个产品，就会产生一个review，取他们的平均值，75左右.
    当我们查看reivew的时候，最好是以半年时间为准。选择最近的review来做计算。
    最近一天的review如果是10个，那一天大概的销量就是750个。
    """

    url = 'https://us.shein.com/goods_detail_nsw/getCommentInfoByAbc'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    }

    _lang = 'en'
    _ver = '1.1.8'
    rule_id = 'recsrch_sort:A'

    goods_id = ''  # 商品颜色
    is_picture = ''  # 包含图片
    comment_rank = ''  # 1 2 3 4 5 星级
    size = ''  # S M L XXL
    limit = 3
    spu: str = 'W2105291888'
    page: int

    query_params = {
        '_lang': _lang,
        '_ver': _ver,
        'rule_id': rule_id,
    }

    def __init__(self, spu, limit=3):
        self.limit = limit
        self.query_params['spu'] = spu
        self.query_params['limit'] = limit

    def get_once(self, page=1, meta=None):
        self.query_params['page'] = page
        self.query_params['offset'] = (page - 1) * self.limit
        url = self.url + "?" + urlencode(self.query_params)
        return Request(
            url,
            callback=self.parse,
            meta=meta
            # headers=self.headers
        )
        # print(response.status_code)

    def parse(self, response: TextResponse):

        item = response.meta['item']

        rdata = response.json()
        rinfo = rdata['info']
        msg = rdata['msg']  # ok
        print(msg)
        reviews_list_res = rinfo['commentInfo']
        reviews_list = []
        for rreview in reviews_list_res:
            # image = rreview['comment_image'][0]['member_image_original']
            review = {
                'comment_timestamp': rreview['add_time'],
                'comment_time': rreview['comment_time'],
                'body': rreview['content'],
                'code': rreview['comment_id'],
                'rank': rreview['comment_rank'],
                'color': rreview['color'],
                'goods_code': rreview['goods_id'],
                'spu': rreview['spu'],
                'order_timestamp': rreview['order_timestamp'],
                'order_time': rreview['order_time'],
                'size': rreview['size'],
                'member_overall_fit': rreview['member_overall_fit']  # 1 合身 2 偏大  size_status member_size_flag
            }
            print(review['member_overall_fit'])
            print(review['size'])
            print(review['color'])
            print(review['body'])
            print('====================')
            reviews_list.append(review)

        total = rinfo['commentInfoTotal']  # allTotal
        item['reviews_num'] = total
        yield item
        print(total)
        # total_picture = rinfo['pictureTotal']
        # print(total_picture)
        # print(rinfo['num'])
        # print(len(reviews_list_res))
        # return reviews_list



