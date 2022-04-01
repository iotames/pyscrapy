import re
from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem, GoodsReviewItem

from pyscrapy.models import Goods, RankingLog, RankingGoods, ReviewsUpdateLog, GoodsReview
import json
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
from pyscrapy.enum.spider import *
from urllib.parse import urlencode
from scrapy.selector import Selector, SelectorList
from time import strptime, mktime, time
from datetime import datetime
from pyscrapy.items import GoodsReviewShefitItem
from pyscrapy.enum.spider import REVIEWED_TIME_IN


class FashionnovaSpider(BaseSpider):

    name = 'fashionnova'

    base_url = "https://www.fashionnova.com"

    # products_recently_ordered_count_desc products_published_at_desc
    sort = "products_recently_ordered_count_desc"
    collection = "activewear-lounge"
    limit = 48
    total_page_goods_list = 1

    RANK_TYPE_NEW = 1
    RANK_TYPE_BESTSELLERS = 0

    rank_type_map = {
        "products_recently_ordered_count_desc": 0,
        "products_published_at_desc": 1
    }

    custom_settings = {
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': []
    }

    def __init__(self, name=None, **kwargs):
        super(FashionnovaSpider, self).__init__(name=name, **kwargs)
        base_url = "https://www.fashionnova.com"
        self.image_referer = self.base_url + "/"
        self.allowed_domains.append("xn5vepvd4i-2.algolianet.com")
        self.allowed_domains.append("api-cdn.yotpo.com")
    
    def request_goods_list(self, page: int):
        url = f"https://xn5vepvd4i-2.algolianet.com/1/indexes/{self.sort}/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.3.0)%3B%20Browser"
        headers = {
            "origin": self.base_url,
            'referer': self.image_referer,
            'Content-Type': 'application/x-www-form-urlencoded',
            "x-algolia-api-key": "0e7364c3b87d2ef8f6ab2064f0519abb",
            "x-algolia-application-id": "XN5VEPVD4I"
        }
        form_data = {
            "query":"","userToken":"anonymous-6c37c795-a02f-42f6-9bd6-d057d0acf220","ruleContexts":["collection",self.collection],
            "analyticsTags":["collection",self.collection,"desktop","Returning","Hong Kong SAR"],"clickAnalytics":True,"distinct":1,
            "page":page-1,"hitsPerPage":self.limit,"facetFilters":[f"collections:{self.collection}"],
            "facetingAfterDistinct":True,"attributesToRetrieve":["handle","image","title"],"personalizationImpact":0
        }
        post_data = json.dumps(form_data, separators=(',', ':'))
        return Request(url,
            method="POST",headers=headers,
            body=post_data,
            # cookies=cookies,
            meta=dict(page=page),
            callback=self.parse_goods_list
        )

    def start_requests(self):
        if self.spider_child == CHILD_GOODS_LIST_RANKING:
            category_name = self.input_args["category_name"] if 'category_name' in self.input_args else ""
            if category_name != "":
                self.collection = category_name
            sort = self.input_args["sort"] if "sort" in self.input_args else ""
            if sort != "":
                self.sort = sort
            total_page = int(self.input_args["total_page"]) if "total_page" in self.input_args else 1
            if total_page > 1:
                self.total_page_goods_list = total_page
            
            goods_list_url = self.input_args['url'] if 'url' in self.input_args else ""
            ranking_log_id = int(self.input_args['ranking_log_id']) if 'ranking_log_id' in self.input_args else 0
            if ranking_log_id:
                self.ranking_log_id = ranking_log_id
            else:
                self.create_ranking_log(category_name, self.rank_type_map[self.sort])
                RankingLog.save_update({"id": self.ranking_log_id}, {"url": goods_list_url})
            yield self.request_goods_list(1)

        if self.spider_child == CHILD_GOODS_REVIEWS_BY_RANKING:
            if 'ranking_log_id' not in self.input_args:
                raise RuntimeError("缺少ranking_log_id参数")
            self.ranking_log_id = int(self.input_args['ranking_log_id'])
            ranking_goods_list = RankingGoods.get_all_model(self.db_session, {'ranking_log_id': self.ranking_log_id})
            print('==================goods_list_len = ' + str(len(ranking_goods_list)))
            for xgd in ranking_goods_list:
                model = Goods.get_model(self.db_session, {'id': xgd.goods_id})
                yield Request(f"{model.url}.js", method="GET",meta=dict(goods_model=model), callback=self.parse_goods_detail)

    def request_goods_reviews(self, meta: dict) -> Request:
        goods_model = meta['goods_model']
        url = "https://api-cdn.yotpo.com/v1/reviews/bBxKixoakwLbMRVuO8JhTHZFlwJXaFEwHIaOVnG5/filter.json"
        post_data = {"domain_key":goods_model.code,"per_page":meta['limit'],"page":meta['page'],"sortings":[{"sort_by":"date","ascending":False}]}
        post_data = json.dumps(post_data, separators=(',', ':'))
        headers = {
            "origin": self.base_url,
            "referer": self.image_referer,
            "accept": "application/json",
            "content-type": "application/json",
        }
        print(f"--request-reviews------page:{str(meta['page'])}---post_data:{post_data}---")
        return Request(url, method='POST', headers=headers, body=post_data, meta=meta, callback=self.parse_goods_reviews)

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        json_info = response.json()
        goods_items = json_info['hits']
        goods_list_len = len(goods_items)  # 48
        print('=========total goods =======' + str(goods_list_len))
        i = 1
        for goods in goods_items:
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            code = goods['_highlightResult']['id']['value']
            goods_item['code'] = code
            goods_item['title'] = goods['title']
            goods_item['url'] = self.get_site_url(f"/products/{goods['handle']}")
            image = goods['image'].replace(".jpg", "_200x.jpg")
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            rank_num = (page-1)*self.limit + i
            goods_item['details'] = {'rank_num': rank_num}
            i += 1
            yield goods_item
        
        if page < self.total_page_goods_list:
            yield self.request_goods_list(page+1)


    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        goods_model = meta['goods_model']
        resp = response.json()
        goods_item = BaseGoodsItem()
        goods_item['spider_name'] = self.name
        goods_item['model'] = goods_model
        goods_item['price'] = resp['price']/100
        
        meta['goods_item'] = goods_item
        meta['limit'] = 3
        meta['page'] = 1
        yield self.request_goods_reviews(meta)
    
    def parse_goods_reviews(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        limit = meta['limit']
        goods_model = meta['goods_model']

        is_log_exist = ReviewsUpdateLog.is_exists_by_spu(self.site_id, goods_model.code)
        
        print(f"======parse_goods_reviews======page={str(page)}=========")
        resp = response.json()
        resp = resp["response"]
        # print(resp)
        
        reviews_num = resp['pagination']['total']
        print(f"----goods_id---total-reviews------{str(goods_model.id)}--{str(reviews_num)}-----")
        if page == 1:
            goods_item = meta['goods_item']
            goods_item['reviews_num'] = reviews_num
            yield goods_item

        reviews = resp['reviews']
        for review in reviews:
            review_item = GoodsReviewItem()
            review_item['goods_id'] = goods_model.id
            review_item['goods_code'] = goods_model.code
            # review_item['goods_spu'] = goods_model.code

            review_item['title'] = review['title']
            review_item['code'] = review['id']
            review_item['rating_value'] = review['score']
            review_item['body'] = review['content']

            time_str = review['created_at']  # "2022-03-30T03:25:59.000Z"
            dtime = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.000Z")
            timestamp = dtime.timestamp()  # mktime(dtime)
            review_item['review_date'] = dtime
            review_item['review_time'] = timestamp

            is_recent = True
            

            old_timestamp = int(time()) - REVIEWED_TIME_IN
            if timestamp < old_timestamp:
                # 评论日期太久远
                is_recent = False
            
            is_review_exist = False
            model = GoodsReview.get_model(self.db_session, {'code': review_item['code'], 'site_id': self.site_id})
            if model:
                review_item['model'] = model
                is_review_exist = True
            
            yield review_item
        
        if (not self.is_last_page(reviews_num, page, limit)) and is_recent and (not (is_review_exist and is_log_exist)):
            if limit == 3 and page == 1:
                meta['limit'] = 10
            else:
                meta['page'] += 1
            yield self.request_goods_reviews(meta)
        else:
            print(f"------reviews--get--end---id,total_reviews---{goods_model.id}--{reviews_num}------")
            ReviewsUpdateLog.add_log(goods_model)

    def is_last_page(self, reviews_num, page, limit) -> bool:
        total_page = reviews_num // limit
        remainder = reviews_num % limit
        if remainder > 0:
            total_page += 1
        if page < total_page:
            return False
        return True

