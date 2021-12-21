import datetime
import time

from scrapy.http import TextResponse
from scrapy import Request
from urllib.parse import urlencode
from pyscrapy.database import Database
from sqlalchemy.orm.session import Session
from Config import Config
from pyscrapy.models import Goods, GoodsReview
import copy
from pyscrapy.items import GoodsReviewSheinItem, BaseGoodsItem
from pyscrapy.enum.spider import REVIEWED_TIME_IN


class ReviewRequest(object):
    """
    大概每销售50-100个产品，就会产生一个review，取他们的平均值，75左右.
    当我们查看reivew的时候，最好是以半年时间为准。选择最近的review来做计算。
    最近一天的review如果是10个，那一天大概的销量就是750个。
    """

    url = 'https://us.shein.com/goods_detail_nsw/getCommentInfoByAbc'

    db_session: Session
    spider = None
    goods_model: Goods
    review_item: GoodsReviewSheinItem
    goods_item: BaseGoodsItem

    data: dict
    headers = None
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
    TYPE_SIMPLE = 'simple'
    filter_type = TYPE_ALL

    process_end = False
    is_review_exists = False
    is_review_too_old = False

    def check_time_old(self, comment_timestamp: int):
        # 判断评论时间是否在有效期之外
        old_time = int(time.time()) - REVIEWED_TIME_IN
        if comment_timestamp < old_time:
            self.is_review_too_old = True
            return True
        return False

    def check_review_exists(self, review_item: GoodsReviewSheinItem):
        db_session = self.db_session
        model = GoodsReview.get_model(db_session, {'code': review_item['code'], 'site_id': self.spider.site_id})
        if model:
            review_item['model'] = model
            print('========is_review_exists==goods_id={}============'.format(str(self.goods_model.id)))
            self.is_review_exists = True
            return True
        return False

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

    def set_from_meta(self, meta):
        goods_model = meta['goods_model'] if 'goods_model' in meta else None
        if not goods_model:
            goods_model = self.db_session.query(Goods).filter(Goods.asin == self.spu).first()
        if not goods_model:
            raise RuntimeError('spu商品不存在')
        self.goods_model = goods_model
        goods_item = meta['goods_item'] if 'goods_item' in meta else BaseGoodsItem()
        self.goods_item = goods_item

    def get_schema(self, meta=None):
        self.filter_type = self.TYPE_SCHEMA
        self.set_from_meta(meta)
        self.limit = 3
        return Request(self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)

    def get_simple(self, meta=None):
        self.filter_type = self.TYPE_SIMPLE
        self.set_from_meta(meta)
        self.limit = 3
        self.sort = self.SORT_ASC
        return Request(self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)

    @property
    def request_url(self):
        return self.url + "?" + urlencode(self.query_params)

    def __init__(self, spu: str, spider, headers=None):
        self.spider = spider
        self.spu = spu
        self.headers = headers
        db = Database(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()

    def get_all(self, meta=None):
        self.filter_type = self.TYPE_ALL
        self.set_from_meta(meta)
        self.limit = 20
        self.sort = self.SORT_DESC
        review_item = GoodsReviewSheinItem()
        review_item['goods_id'] = self.goods_model.id
        review_item['goods_code'] = self.goods_model.code
        self.review_item = review_item
        return Request(self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)

    def get_review_item(self, review: dict, review_base: GoodsReviewSheinItem) -> GoodsReviewSheinItem:
        review_item = copy.copy(review_base)
        review_item['code'] = review['code']
        review_item['rating_value'] = review['rank']
        review_item['sku_text'] = review['color'] + "|" + review['size']
        review_item['color'] = review['color']
        timestamp = int(review['comment_timestamp'])
        review_item['review_time'] = timestamp
        review_item['review_date'] = datetime.datetime.fromtimestamp(timestamp)
        review_item['time_str'] = review['comment_time']
        review_item['body'] = review['body']
        self.check_time_old(timestamp)
        self.check_review_exists(review_item)
        print('=============get_review_item=====goods_id={}======'.format(str(self.goods_model.id)))
        print(review)
        return review_item

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

    def is_last_page(self) -> bool:
        total_reviews = self.data['total']
        had_len = (self.page - 1) * self.limit + len(self.data['items'])
        if total_reviews == had_len:
            return True
        return False

    def parse(self, response: TextResponse):
        print('reviews_parse=====================')
        if response.text == 'null':
            yield self.goods_item
            print('=====================goods_reviews=======null==========')
            return False

        rdata = response.json()
        self.data = self.get_data(rdata)
        data = self.data

        if data['code'] == -1:
            yield self.goods_item
            print('=====================goods_reviews=======code=-1========')
            return False

        total_reviews = data['total']
        self.goods_item['reviews_num'] = total_reviews  # 评论总数
        # 获取首次评论时间
        if self.sort == self.SORT_ASC and self.page == 1:
            first_review_time = data['items'][0]['comment_time']
            self.goods_item['details']['first_review_time'] = first_review_time

        if self.filter_type == self.TYPE_SIMPLE:
            print('=======get simple reviews=========')
            yield self.goods_item

        if self.filter_type == self.TYPE_ALL:
            print('reviews_parse_TYPE_ALL====================')
            for review in data['items']:
                yield self.get_review_item(review, self.review_item)

            if self.is_last_page() or self.is_review_exists or self.is_review_too_old:
                # 切换请求方式。 获取首次评论的时间。 yield self.goods_item
                print('========get all views end=======' + str(self.goods_model.id))
                yield self.get_simple(meta=dict(goods_model=self.goods_model, goods_item=self.goods_item))
            else:
                self.page += 1
                yield Request(url=self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)

        if self.filter_type == self.TYPE_SCHEMA:
            # TODO 似乎陷入了死循环
            # 没有过滤颜色和星级
            if (not self.comment_rank) and (not self.goods_id) and (not data['items']):
                for irank in range(1, 6):
                    self.goods_item['details']['rank_score'][str(irank)] = 0  # {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
                if self.goods_item['details']['relation_colors']:
                    for icolor in range(len(self.goods_item['details']['relation_colors'])):
                        self.goods_item['details']['relation_colors'][icolor]["reviews_num"] = 0
                print('====================111=========')
                self.process_end = True
                yield self.goods_item
            else:
                if not self.comment_rank and not self.process_end:
                    self.comment_rank = 1
                    yield Request(url=self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)

            if self.comment_rank and not self.process_end:
                if self.comment_rank < 5:
                    if 'rank_score' not in self.goods_item['details']:
                        self.goods_item['details']['rank_score'] = {str(self.comment_rank): data['total']}
                    else:
                        self.goods_item['details']['rank_score'][str(self.comment_rank)] = data['total']
                    self.comment_rank += 1
                    yield Request(url=self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)
                else:
                    self.goods_item['details']['rank_score'][str(self.comment_rank)] = data['total']
                    self.comment_rank = ""
                    if self.goods_item['details']['relation_colors']:
                        self.goods_color_index = 0
                        self.goods_id = self.goods_item['details']['relation_colors'][self.goods_color_index]['goods_id']
                        yield Request(url=self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)
                    else:
                        print('==========222==============')
                        self.process_end = True
                        yield self.goods_item

            if self.goods_id and not self.process_end:
                colorii = self.goods_color_index
                self.goods_item['details']['relation_colors'][colorii]["reviews_num"] = data['total']
                if (len(self.goods_item['details']['relation_colors']) - colorii) > 1:
                    goods_id = self.goods_item['details']['relation_colors'][colorii]['goods_id']
                    self.goods_id = goods_id
                    self.goods_color_index += 1
                    yield Request(url=self.request_url, callback=self.parse, headers=self.headers, dont_filter=True)
                else:
                    self.goods_id = ''
                    self.process_end = True
                    print('==========333==============' + str(self.goods_model.id))
                    yield self.goods_item


if __name__ == '__main__':
    print('====')
