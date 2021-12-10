from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config


class AloyogaSpider(BaseSpider):

    # 需要 cookie

    name = 'aloyoga'

    handle_httpstatus_list = [415, 400]

    base_url = "https://www.aloyoga.com"
    API_URL = 'https://www.aloyoga.com/api/2020-10/graphql.json'
    API_TOKEN = 'd7ef45a4f583a78079bfebcb868b5931'

    custom_settings = {
        # 'DEFAULT_REQUEST_HEADERS': {
        #     'USER_AGENT': USER_AGENT,
        # },
        # 'USER_AGENT': USER_AGENT,
        # 'COOKIES_ENABLED': True,
        # 'DOWNLOAD_DELAY': 3,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # default 8
        # 'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
        'SELENIUM_ENABLED': False
    }

    handle_list = [
        # 'tees-tanks',
        'mens-long-sleeves',
    ]

    # KEY_HasNextPage = 'hasNextPage'  # False
    KEY_HasPreviousPage = 'hasPreviousPage'  # False

    KEY_After = 'after'  # str
    KEY_First = 'first'  # 15 39
    KEY_FirstForImages = 'firstForImages'  # 2
    KEY_Handle = 'handle'  # 'tops'

    variables_map = {}

    def create_variables(self, handle):
        self.variables_map[handle] = {
            self.KEY_HasPreviousPage: False
        }
        return self.get_request_variables(handle)

    def set_has_previous_page(self, handle, value: bool):
        self.variables_map[handle][self.KEY_HasPreviousPage] = value

    def get_request_variables(self, handle):
        handle_vars = self.variables_map[handle]
        first = 39 if handle_vars[self.KEY_HasPreviousPage] else 15  # 第一页为 15 否则为 39
        variables = {self.KEY_First: first, self.KEY_FirstForImages: 2, self.KEY_Handle: handle}
        if handle_vars[self.KEY_HasPreviousPage]:
            # 如果不为第一页，必须设置 after 项
            variables[self.KEY_After] = handle_vars[self.KEY_After]
        return variables

    headers = {
        'content-type': 'application/json',
        'x-shopify-storefront-access-token': API_TOKEN,
    }

    def __init__(self, name=None, **kwargs):
        super(AloyogaSpider, self).__init__(name=name, **kwargs)

    def get_request_body(self, handle):
        variables = json.dumps(self.get_request_variables(handle))
        # request_body = r'{"operationName":"plpProducts","variables":{"first":15,"handle":"womens-leggings","firstForImages":2},"query":"query plpProducts($first: Int!, $handle: String!, $after: String, $reverse: Boolean, $sortKey: ProductCollectionSortKeys, $firstForImages: Int!) {\n  collection: collectionByHandle(handle: $handle) {\n    id\n    products(first: $first, after: $after, sortKey: $sortKey, reverse: $reverse) {\n      pageInfo {\n        hasNextPage\n        hasPreviousPage\n        __typename\n      }\n      edges {\n        cursor\n        node {\n          ...PlpProductDetails\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PlpProductDetails on Product {\n  id\n  images(first: $firstForImages, maxWidth: 1) {\n    edges {\n      node {\n        originalSrc\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  tags\n  title\n  priceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  compareAtPriceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  availableForSale\n  handle\n  availableColors: metafield(namespace: \"alo-swatch\", key: \"available-colors\") {\n    value\n    __typename\n  }\n  productType\n  vendor\n  onlineStoreUrl\n  totalInventory\n  options {\n    name\n    values\n    __typename\n  }\n  __typename\n}\n"}'
        request_body = r'{"operationName":"plpProducts","variables":' + variables + r',"query":"query plpProducts($first: Int!, $handle: String!, $after: String, $reverse: Boolean, $sortKey: ProductCollectionSortKeys, $firstForImages: Int!) {\n  collection: collectionByHandle(handle: $handle) {\n    id\n    products(first: $first, after: $after, sortKey: $sortKey, reverse: $reverse) {\n      pageInfo {\n        hasNextPage\n        hasPreviousPage\n        __typename\n      }\n      edges {\n        cursor\n        node {\n          ...PlpProductDetails\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PlpProductDetails on Product {\n  id\n  images(first: $firstForImages, maxWidth: 1) {\n    edges {\n      node {\n        originalSrc\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  tags\n  title\n  priceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  compareAtPriceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  availableForSale\n  handle\n  availableColors: metafield(namespace: \"alo-swatch\", key: \"available-colors\") {\n    value\n    __typename\n  }\n  productType\n  vendor\n  onlineStoreUrl\n  totalInventory\n  options {\n    name\n    values\n    __typename\n  }\n  __typename\n}\n"}'
        return request_body

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for handle in self.handle_list:
                self.create_variables(handle)
                body = self.get_request_body(handle)
                yield Request(self.API_URL, callback=self.parse_goods_list, headers=self.headers, method='POST',
                              body=body, meta=dict(handle=handle))

        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time()
            if self.app_env == self.spider_config.ENV_PRODUCTION:
                before_time = time.time() - (2 * 3600)
            self.goods_model_list = self.db_session.query(Goods).filter(and_(
                Goods.site_id == self.site_id, or_(
                    Goods.status == Goods.STATUS_UNKNOWN,
                    Goods.updated_at < before_time)
            )).all()
            goods_list_len = len(self.goods_model_list)
            print('=======goods_list_len============ : {}'.format(str(goods_list_len)))
            if goods_list_len > 0:
                for model in self.goods_model_list:
                    yield Request(self.get_site_url(model.url), headers={'referer': self.base_url},
                                  callback=self.parse_goods_detail, meta=dict(model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    count_goods_list = 0

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        handle = meta['handle']
        print(response.status)
        print(response.text)
        json_response = json.loads(response.text)
        data = json_response['data']
        if 'collection' not in data:
            return False
        collection = data['collection']  # __typename: "Collection"
        cid = collection['id']
        products = collection['products']  # __typename: "ProductConnection"
        page_info = products['pageInfo']  # {hasNextPage: true, hasPreviousPage: false, __typename: "PageInfo"}

        edges = products['edges']
        for edge in edges:
            self.count_goods_list += 1
            product_cursor = edge['cursor']
            product = edge['node']
            """ products_edges_node
            handle: "w5604r-7-8-high-waist-airbrush-legging-black"
            id: "Z2lkOi8vc2hvcGlmeS9Qcm9kdWN0LzYyMzk5MTEzNDYzNTY="
            onlineStoreUrl: "https://www.aloyoga.com/products/w5604r-7-8-high-waist-airbrush-legging-black"
            options: [
                {name: "Color", values: ["Black"], __typename: "ProductOption"}, 
                {name: "Size", values: ["XXS", "XS", "S", "M", "L", "XL"], __typename: "ProductOption"}
            ]
            priceRange
            productType: "Women:Bottoms:Leggings"
            totalInventory: 19674
            vendor: "Alo Yoga"
            """
            image_node = self.get_nodes_by_collection(product['images'])[0]
            # https://cdn.shopify.com/s/files/1/2185/2813/products/W5604R_01_b2_s1_a1_m76_1x.jpg?v=1636654481
            original_src = image_node['originalSrc']
            img_tmp = original_src.split('?')
            if len(img_tmp) > 1:
                original_src = img_tmp[0]
            image = original_src.replace('_1x.jpg', '_320x.jpg')
            title = product['title']
            url = product['onlineStoreUrl']
            print(title)
            colors_str = product['availableColors']['value']
            colors = json.loads(colors_str)
            print('============colors_len ====' + str(len(colors)))
            print(colors)
            status = Goods.STATUS_UNAVAILABLE
            if product['availableForSale']:
                status = Goods.STATUS_AVAILABLE
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['image'] = image
            goods_item['image_urls'] = [image]
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['category_name'] = product['productType']
            goods_item['status'] = status
            yield goods_item
        # self.set_has_previous_page(handle, page_info['hasPreviousPage'])
        # if page_info['hasNextPage']:
        #     body = self.get_request_body(handle)
        #     yield Request(self.API_URL, callback=self.parse_goods_list, headers=self.headers, method='POST',
        #                   body=body, meta=dict(handle=handle))
        print('=========total_goods_list len = ' + str(self.count_goods_list))

    @staticmethod
    def get_nodes_by_collection(collection: dict) -> list:
        edges = collection['edges']
        nodes = []
        for edge in edges:
            nodes.append(edge['node'])
        return nodes

    statuses = {
        'InStock': Goods.STATUS_AVAILABLE,
        'SoldOut': Goods.STATUS_SOLD_OUT,
        'OutOfStock': Goods.STATUS_SOLD_OUT,
        'Discontinued': Goods.STATUS_UNAVAILABLE
    }

    def parse_goods_detail(self, response: TextResponse):
        meta = response.meta
        model = meta['model']
        # availableQuantity 库存
        pass


