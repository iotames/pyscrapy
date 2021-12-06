from scrapy.http import TextResponse
from scrapy import Request
from urllib.parse import urlencode
from pyscrapy.database import Database
from sqlalchemy.orm.session import Session
from Config import Config
from pyscrapy.models import Goods
import copy
from pyscrapy.items import GoodsReviewItem, BaseGoodsItem


class ReviewRequest(object):
    """
    大概每销售50-100个产品，就会产生一个review，取他们的平均值，75左右.
    当我们查看reivew的时候，最好是以半年时间为准。选择最近的review来做计算。
    最近一天的review如果是10个，那一天大概的销量就是750个。
    """

    url = 'https://us.shein.com/goods_detail_nsw/getCommentInfoByAbc'

    db_session: Session

    data: dict

    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    # }

    SORT_ASC = 'time_asc'
    SORT_DESC = 'time_desc'
    SORT_DEFAULT = ''

    _lang = 'en'
    _ver = '1.1.8'
    rule_id = 'recsrch_sort:A'

    page = 1
    goods_id = ''  # 商品颜色
    is_picture = ''  # 包含图片
    comment_rank = ''  # 1 2 3 4 5 星级
    size = ''  # S M L XXL
    sort = SORT_ASC  # 排序： time_asc 时间顺序(由远及近); time_desc 时间逆序; default ''
    limit = 3
    tag_id = ''

    spu: str
    goods_color_index: int

    TYPE_ALL = 'all'
    TYPE_SCHEMA = 'schema'
    TYPE_UPDATE = 'update'
    TYPE_SIMPLE = 'simple'
    filter_type = TYPE_ALL

    @property
    def query_params(self):
        params = {
            '_lang': self._lang,
            '_ver': self._ver,
            'rule_id': self.rule_id,
            'sort': self.sort,
            'limit': self.limit,
            'page': self.page,
            'size': self.size,
            'spu': self.spu,
            'offset': (self.page - 1) * self.limit,
            'goods_id': self.goods_id,
            'is_picture': self.is_picture,
            'tag_id': self.tag_id
        }
        if self.comment_rank:
            params['comment_rank'] = self.comment_rank
        return params

    def get_schema(self, meta=None):
        self.filter_type = self.TYPE_SCHEMA
        self.limit = 3
        return Request(self.request_url, callback=self.parse, meta=meta, dont_filter=True)

    def get_simple(self, meta=None):
        self.filter_type = self.TYPE_SIMPLE
        self.limit = 3
        return Request(self.request_url, callback=self.parse, meta=meta, dont_filter=True)

    @property
    def request_url(self):
        return self.url + "?" + urlencode(self.query_params)

    def __init__(self, spu: str):
        self.spu = spu
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

    def get_all(self, meta=None):
        goods_model = meta['goods_model'] if 'goods_model' in meta else None
        if not goods_model:
            goods_model = self.db_session.query(Goods).filter(Goods.asin == self.spu).first()
        if not goods_model:
            raise RuntimeError('spu商品不存在')
        self.filter_type = self.TYPE_ALL
        self.limit = 100
        review_item = GoodsReviewItem()
        review_item['goods_id'] = goods_model.id
        review_item['goods_code'] = goods_model.code

        goods_item = meta['goods_item'] if 'goods_item' in meta else BaseGoodsItem()
        meta = {'review_item': review_item, 'goods_item': goods_item}
        return Request(self.request_url, callback=self.parse, meta=meta, dont_filter=True)

    def update(self):
        self.filter_type = self.TYPE_UPDATE
        self.limit = 100
        self.sort = self.SORT_DESC
        goods_model = self.db_session.query(Goods).filter(Goods.asin == self.spu).first()
        if not goods_model:
            raise RuntimeError('spu商品不存在')
        review_item = GoodsReviewItem()
        review_item['goods_id'] = goods_model.id
        review_item['goods_code'] = goods_model.code
        goods_item = BaseGoodsItem()
        meta = {'review_item': review_item, 'goods_item': goods_item}
        return Request(self.request_url, callback=self.parse, meta=meta, dont_filter=True)

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
        # total_picture = rinfo['pictureTotal']
        # print(total_picture)
        # print(rinfo['num'])
        return dict(code=0, msg='ok', total=total, items=items)

    def next_process(self, meta, data: dict):
        reviews_list = data['items']
        item = meta['goods_item']
        if not self.goods_id and not self.comment_rank and not self.size:
            item['reviews_num'] = data['total']
            if self.sort == self.SORT_ASC and self.page == 1:
                first_review_time = reviews_list[0]['comment_time']
                item['details']['first_review_time'] = first_review_time
        # query_params = meta['query_params'].copy()
        # for i in range(1, 6):
        # 1星评论
        return Request(
            url=self.request_url,
            callback=self.parse,
            meta=dict(goods_item=item),
            dont_filter=True
        )

    def is_last_page(self) -> bool:
        total_reviews = self.data['total']
        had_len = (self.page - 1) * self.limit + len(self.data['items'])
        if total_reviews == had_len:
            return True
        return False

    def parse(self, response: TextResponse):
        meta = response.meta
        item = meta['goods_item']
        if response.text == 'null':
            yield item
            print('=====================goods_reviews=======null==========')
            return False

        rdata = response.json()
        self.data = self.get_data(rdata)
        data = self.data

        if data['code'] == -1:
            yield item
            print('=====================goods_reviews=======code=-1========')
            return False

        total_reviews = data['total']
        item['reviews_num'] = total_reviews

        if self.filter_type == self.TYPE_SIMPLE:
            yield item

        if self.filter_type == self.TYPE_UPDATE:
            yield item

        if self.filter_type == self.TYPE_ALL:
            review_base = meta['review_item']

            for review in data['items']:
                review_item = copy.copy(review_base)
                review_item['rating_value'] = review['rank']
                review_item['sku_text'] = review['color'] + "|" + review['size']
                review_item['color'] = review['color']
                review_item['review_date'] = review['comment_time']
                review_item['body'] = review['body']
                yield review_item

            item['reviews_num'] = total_reviews
            if self.is_last_page():
                #  review_item
                yield item
            else:
                self.page += 1
                yield self.next_process(meta, data)

        if self.filter_type == self.TYPE_SCHEMA:
            # 没有过滤颜色和星级
            if not self.comment_rank and not self.goods_id and not data['items']:
                for irank in range(1, 6):
                    item['details']['rank_score'][str(irank)] = 0  # {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                if item['details']['relation_colors']:
                    for icolor in range(len(item['details']['relation_colors'])):
                        item['details']['relation_colors'][icolor]["reviews_num"] = 0
                yield item
            else:
                self.comment_rank = 1
                yield self.next_process(meta, data)

            if self.comment_rank:
                if self.comment_rank < 5:
                    if 'rank_score' not in item['details']:
                        item['details']['rank_score'] = {str(self.comment_rank): data['total']}
                    else:
                        item['details']['rank_score'][str(self.comment_rank)] = data['total']
                    self.comment_rank += 1
                    meta['goods_item'] = item
                    yield self.next_process(meta, data)
                else:
                    item['details']['rank_score'][str(self.comment_rank)] = data['total']
                    self.comment_rank = ""
                    if item['details']['relation_colors']:
                        self.goods_color_index = 0
                        self.goods_id = item['details']['relation_colors'][self.goods_color_index]['goods_id']
                        meta['goods_item'] = item
                        yield self.next_process(meta, data)
                    else:
                        yield item

            if self.goods_id:
                query_params = meta['query_params'].copy()
                colorii = self.goods_color_index
                item['details']['relation_colors'][colorii]["reviews_num"] = data['total']
                if (len(item['details']['relation_colors']) - colorii) > 1:
                    goods_id = item['details']['relation_colors'][colorii]['goods_id']
                    query_params['goods_id'] = goods_id
                    self.goods_color_index += 1
                    yield self.next_process(meta, data)
                else:
                    yield item


if __name__ == '__main__':
    rev = ReviewRequest("W2004101375").get_all()
