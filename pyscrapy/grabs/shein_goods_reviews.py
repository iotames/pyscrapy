from scrapy.http import TextResponse
from scrapy import Request
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

    page = 1
    goods_id = ''  # 商品颜色
    is_picture = ''  # 包含图片
    comment_rank = ''  # 1 2 3 4 5 星级
    size = ''  # S M L XXL
    sort = 'time_asc'  # 排序： time_asc 时间顺序(由远及近); time_desc 时间逆序; default ''
    limit = 3

    query_params = {
        '_lang': _lang,
        '_ver': _ver,
        'rule_id': rule_id,
        'sort': sort,
        'limit': limit,
        'page': page,
        'comment_rank': comment_rank
    }

    @classmethod
    def get_once(cls, data: dict, meta=None):
        # self.query_params['spu'] = spu
        cls.query_params.update(data)
        cls.query_params['offset'] = (cls.query_params['page'] - 1) * cls.query_params['limit']
        url = cls.url + "?" + urlencode(cls.query_params)
        meta['query_params'] = cls.query_params
        print('get_once=========' + meta['goods_url'])

        return Request(
            url,
            callback=cls.parse,
            meta=meta,
            dont_filter=True
            # headers=self.headers
        )

    # @classmethod
    # def next_next(cls, rdata, item, meta):

    @classmethod
    def parse(cls, response: TextResponse):
        # TODO 使用 return False 造成中断，导致数据采集不完整?? 其他原因？？......
        meta = response.meta
        print('=============test meta================')
        print(meta)
        print('ReviewRequest===parse=========' + meta['goods_url'])
        item = meta['item']
        next_next = True
        if response.text == 'null':
            yield item
            print('=====================goods_reviews=======null==============================' + meta['goods_url'])
            next_next = False

        if next_next:
            rdata = response.json()
            if rdata['code'] == -1:
                yield item
                print('=====================goods_reviews=======code=-1==========================' + meta['goods_url'])
                next_next = False

            if next_next:
                # return cls.next_next(rdata, item, meta): # TODO  yield return ...... ?
                rinfo = rdata['info']
                msg = rdata['msg']  # ok
                print('======================goods_reviews: ' + msg)
                reviews_list = []
                first_review_time = ""
                for rreview in rinfo['commentInfo']:
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
                    if first_review_time == "":
                        first_review_time = review['comment_time']
                    reviews_list.append(review)

                total = rinfo['commentInfoTotal']  # allTotal

                if 'get_total_rank1' in meta:
                    item['details']['total_rank1'] = total
                    yield item
                else:
                    item['reviews_num'] = total
                    item['details']['first_review_time'] = first_review_time
                    query_params = meta['query_params'].copy()
                    query_params['comment_rank'] = 1
                    yield Request(
                        url=cls.url + "?" + urlencode(query_params),
                        callback=cls.parse,
                        meta=dict(item=item, get_total_rank1=True, goods_url=meta['goods_url']),
                        dont_filter=True
                    )
        # total_picture = rinfo['pictureTotal']
        # print(total_picture)
        # print(rinfo['num'])
        # return reviews_list



