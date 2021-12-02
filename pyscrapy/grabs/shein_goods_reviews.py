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

    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    # }

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

        return Request(
            url,
            callback=cls.parse,
            meta=meta,
            dont_filter=True
            # headers=self.headers
        )

    @classmethod
    def get_data(cls, rdata: dict) -> dict:
        if rdata['code'] == -1:
            return dict(code=-1, msg=rdata['msg'])
        items = []
        rinfo = rdata['info']
        for rreview in rinfo['commentInfo']:
            # image = rreview['comment_image'][0]['member_image_original']
            review = {
                'comment_timestamp': rreview['add_time'],
                'comment_time': rreview['comment_time'],
                'body': rreview['content'],  # 评论内容主体
                'code': rreview['comment_id'],
                'rank': rreview['comment_rank'],
                'color': rreview['color'],  # 颜色
                'goods_code': rreview['goods_id'],
                'spu': rreview['spu'],
                'order_timestamp': rreview['order_timestamp'] if 'order_timestamp' in rreview else 0,
                'order_time': rreview['order_time'],
                'size': rreview['size'],  # 尺码
                'member_overall_fit': rreview['member_overall_fit']  # 1 合身 2 偏大  size_status member_size_flag
            }
            items.append(review)
        total = rinfo['commentInfoTotal']  # allTotal
        return dict(code=0, msg='ok', total=total, items=items)

    @classmethod
    def parse(cls, response: TextResponse):
        meta = response.meta
        item = meta['item']
        # next_next = True
        if response.text == 'null':
            yield item
            print('=====================goods_reviews=======null==========')
            return False
            # next_next = False

        # if next_next:
        rdata = response.json()
        if rdata['code'] == -1:
            yield item
            print('=====================goods_reviews=======code=-1========')
            return False

        data = cls.get_data(rdata)
        reviews_list = data['items']
        if ('color_goods_index' not in meta) and ('comment_rank' not in meta):
            # 没有过滤颜色和星级
            if reviews_list:
                item['details']['first_review_time'] = reviews_list[0]['comment_time']
                item['reviews_num'] = data['total']
                query_params = meta['query_params'].copy()
                # for i in range(1, 6):
                # 1星评论
                query_params['comment_rank'] = 1
                yield Request(
                    url=cls.url + "?" + urlencode(query_params),
                    callback=cls.parse,
                    meta=dict(item=item, query_params=query_params, comment_rank=1),
                    dont_filter=True
                )
            else:
                # 列表为空
                for irank in range(1, 6):
                    item['details']['rank_score'][str(irank)] = 0  # {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                if item['details']['relation_colors']:
                    for icolor in range(len(item['details']['relation_colors'])):
                        item['details']['relation_colors'][icolor]["reviews_num"] = 0
                yield item

        if 'comment_rank' in meta:
            rank = meta['comment_rank']
            if rank < 5:
                if 'rank_score' not in item['details']:
                    item['details']['rank_score'] = {str(rank): data['total']}
                else:
                    item['details']['rank_score'][str(rank)] = data['total']
                query_params = meta['query_params'].copy()
                query_params['comment_rank'] += 1
                rank += 1
                yield Request(
                    url=cls.url + "?" + urlencode(query_params),
                    callback=cls.parse,
                    meta=dict(item=item, query_params=query_params, comment_rank=rank),
                    dont_filter=True
                )
            else:
                item['details']['rank_score'][str(rank)] = data['total']
                query_params = meta['query_params'].copy()
                del query_params['comment_rank']
                if item['details']['relation_colors']:
                    goods_id = item['details']['relation_colors'][0]['goods_id']
                    query_params['goods_id'] = goods_id
                    yield Request(
                        url=cls.url + "?" + urlencode(query_params),
                        callback=cls.parse,
                        meta=dict(item=item, query_params=query_params, color_goods_index=0),
                        dont_filter=True
                    )
                else:
                    yield item

        if 'color_goods_index' in meta:
            query_params = meta['query_params'].copy()
            colorii = meta['color_goods_index']
            item['details']['relation_colors'][colorii]["reviews_num"] = data['total']
            if (len(item['details']['relation_colors']) - colorii) > 1:
                goods_id = item['details']['relation_colors'][colorii]['goods_id']
                query_params['goods_id'] = goods_id
                colorii += 1
                yield Request(
                    url=cls.url + "?" + urlencode(query_params),
                    callback=cls.parse,
                    meta=dict(item=item, query_params=query_params, color_goods_index=colorii),
                    dont_filter=True
                )
            else:
                yield item
        # total_picture = rinfo['pictureTotal']
        # print(total_picture)
        # print(rinfo['num'])


