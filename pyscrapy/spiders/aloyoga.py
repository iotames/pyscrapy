from scrapy.http import TextResponse
from scrapy import Request
from pyscrapy.items import BaseGoodsItem
from pyscrapy.models import Goods
import json
from sqlalchemy import and_, or_
import time
from pyscrapy.spiders.basespider import BaseSpider
from Config import Config
import re


class AloyogaSpider(BaseSpider):

    # 不需要 cookie

    name = 'aloyoga'

    # handle_httpstatus_list = [415, 400]

    base_url = "https://www.aloyoga.com"
    API_URL = 'https://www.aloyoga.com/api/2020-10/graphql.json'
    API_TOKEN = 'd7ef45a4f583a78079bfebcb868b5931'

    custom_settings = {
        # 'DEFAULT_REQUEST_HEADERS': {
        #     'USER_AGENT': USER_AGENT,
        # },
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36",
        # 'COOKIES_ENABLED': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        # 'COMPONENTS_NAME_LIST_DENY': ['user_agent'],
    }

    handle_list = [
        # 'tops',  # https://www.aloyoga.com/collections/tops 318 Products
        "bras-tops",
        'bottoms',  # https://www.aloyoga.com/collections/bottoms 285 Products
        'jackets-coverups',  # https://www.aloyoga.com/collections/jackets-coverups 176 Products
        # 'tees-tanks',  # https://www.aloyoga.com/collections/tees-tanks 102 Products
        # 'shorts-pants',  # https://www.aloyoga.com/collections/shorts-pants 146 Products
        # 'outerwear',  # https://www.aloyoga.com/collections/outerwear 123 Products
    ]

    # KEY_HasNextPage = 'hasNextPage'  # False
    KEY_HasPreviousPage = 'hasPreviousPage'  # False

    KEY_After = 'after'  # str
    KEY_First = 'first'  # 15 39
    KEY_FirstForImages = 'firstForImages'  # 2
    KEY_Handle = 'handle'  # 'tops'

    variables_map = {}

    def create_variables_items(self, handle):
        self.variables_map[handle] = {
            self.KEY_HasPreviousPage: False
        }
        return self.get_request_variables(handle)

    @staticmethod
    def create_variables_detail(spu: str):
        # M1182R
        variables = {"productSearchQuery": "tag:'StyleId:{}' tag:'pricing:fullprice' ".format(spu.upper())}
        return variables

    def set_has_previous_page(self, handle, value: bool):
        self.variables_map[handle][self.KEY_HasPreviousPage] = value

    def set_after(self, handle: str, cursor: str):
        self.variables_map[handle][self.KEY_After] = cursor

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
        self.allowed_domains.append('api.yotpo.com')

    def get_request_body(self, keyword):
        variables = json.dumps(self.get_request_variables(keyword))
        request_body = ''
        if self.spider_child == self.CHILD_GOODS_DETAIL:
            variables_str = json.dumps(self.create_variables_detail(keyword))
            request_body = r'{"operationName":"colorwayProducts","variables":' + variables_str + r',"query":"query colorwayProducts($productSearchQuery: String!) {\n  products(first: 80, query: $productSearchQuery) {\n    edges {\n      node {\n        ...ProductDetails\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ProductDetails on Product {\n  id\n  title\n  productType\n  onlineStoreUrl\n  tags\n  vendor\n  media(first: 250) {\n    edges {\n      node {\n        ... on Video {\n          id\n          sources {\n            width\n            height\n            url\n            mimeType\n            format\n            __typename\n          }\n          previewImage {\n            id\n            transformedSrc\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  attributes: metafields(namespace: \"attribs\", first: 10) {\n    edges {\n      node {\n        key\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  images(first: 25) {\n    edges {\n      node {\n        url: transformedSrc(maxWidth: 750)\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  variants(first: 25) {\n    edges {\n      node {\n        id\n        sku\n        selectedOptions {\n          name\n          value\n          __typename\n        }\n        image {\n          url: transformedSrc(maxWidth: 750)\n          __typename\n        }\n        priceV2 {\n          amount\n          __typename\n        }\n        compareAtPriceV2 {\n          amount\n          __typename\n        }\n        requiresShipping\n        availableForSale\n        quantityAvailable\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  availableForSale\n  handle\n  totalInventory\n  __typename\n}\n"}'
        if self.spider_child == self.CHILD_GOODS_LIST:
            request_body = r'{"operationName":"plpProducts","variables":' + variables + r',"query":"query plpProducts($first: Int!, $handle: String!, $after: String, $reverse: Boolean, $sortKey: ProductCollectionSortKeys, $firstForImages: Int!) {\n  collection: collectionByHandle(handle: $handle) {\n    id\n    products(first: $first, after: $after, sortKey: $sortKey, reverse: $reverse) {\n      pageInfo {\n        hasNextPage\n        hasPreviousPage\n        __typename\n      }\n      edges {\n        cursor\n        node {\n          ...PlpProductDetails\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PlpProductDetails on Product {\n  id\n  images(first: $firstForImages, maxWidth: 1) {\n    edges {\n      node {\n        originalSrc\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  tags\n  title\n  priceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  compareAtPriceRange {\n    maxVariantPrice {\n      amount\n      __typename\n    }\n    minVariantPrice {\n      amount\n      __typename\n    }\n    __typename\n  }\n  availableForSale\n  handle\n  availableColors: metafield(namespace: \"alo-swatch\", key: \"available-colors\") {\n    value\n    __typename\n  }\n  productType\n  vendor\n  onlineStoreUrl\n  totalInventory\n  options {\n    name\n    values\n    __typename\n  }\n  __typename\n}\n"}'
        return request_body

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST:
            for handle in self.handle_list:
                self.create_variables_items(handle)
                body = self.get_request_body(handle)
                yield Request(self.API_URL, callback=self.parse_goods_list, headers=self.headers, method='POST',
                              body=body, meta=dict(handle=handle))

        if self.spider_child == self.CHILD_GOODS_DETAIL:
            # 2小时内的采集过的商品不会再更新
            before_time = time.time()
            # if self.app_env == self.spider_config.ENV_PRODUCTION:
            #     before_time = time.time() - (2 * 3600)
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
                                  callback=self.parse_goods_detail, meta=dict(goods_model=model))
            else:
                raise RuntimeError('待更新的商品数量为0, 退出运行')

    count_goods_list = 0

    def parse_goods_list(self, response: TextResponse):
        meta = response.meta
        handle = meta['handle']
        json_response = json.loads(response.text)
        data = json_response['data']
        if 'collection' not in data:
            return False
        collection = data['collection']  # __typename: "Collection"
        cid = collection['id']
        products = collection['products']  # __typename: "ProductConnection"
        page_info = products['pageInfo']  # {hasNextPage: true, hasPreviousPage: false, __typename: "PageInfo"}
        print('====================page info===========')
        print(page_info)
        edges = products['edges']
        for edge in edges:
            # product_cursor = edge['cursor']
            product = edge['node']
            """ products_edges_node
            handle: "w5604r-7-8-high-waist-airbrush-legging-black"
            id: "Z2lkOi8vc2hvcGlmeS9Qcm9kdWN0LzYyMzk5MTEzNDYzNTY="
            onlineStoreUrl: "https://www.aloyoga.com/products/w5604r-7-8-high-waist-airbrush-legging-black"
            options: [
                {name: "Color", values: ["Black"], __typename: "ProductOption"}, 
                {name: "Size", values: ["XXS", "XS", "S", "M", "L", "XL"], __typename: "ProductOption"}
            ]
            priceRange: {maxVariantPrice: {amount: "82.0", __typename: "MoneyV2"}, minVariantPrice: {amount: "82.0", __typename: "MoneyV2"}}
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
            if not url:
                print('====WARNING!!!!!!============not_url==========================')
                print(edge)
                continue
            print(url)
            self.count_goods_list += 1
            colors_str = product['availableColors']['value']
            colors_list = json.loads(colors_str)
            print('============colors_len ====' + str(len(colors_list)))
            print(colors_list)
            colors_info_list = []
            for color in colors_list:
                value = {'name': color['name'], 'price': color['price'], 'inventory_by_size': color['inventoryBySize'],
                         'total_inventory': color['totalInventory']}
                colors_info_list.append(value)
            status = Goods.STATUS_UNAVAILABLE
            if product['availableForSale']:
                status = Goods.STATUS_AVAILABLE
            price = product['priceRange']['minVariantPrice']['amount']
            details = {
                'price_range': [price, product['priceRange']['maxVariantPrice']['amount']],
                'vendor': product['vendor'],
                'colors': colors_info_list,
            }
            product_handle = product['handle']
            spu = product_handle.split('-')[0]
            goods_item = BaseGoodsItem()
            goods_item['spider_name'] = self.name
            goods_item['asin'] = spu
            goods_item['image'] = image
            goods_item['price'] = price
            goods_item['image_urls'] = [image]
            goods_item['title'] = title
            goods_item['url'] = url
            goods_item['details'] = details
            goods_item['category_name'] = product['productType']
            goods_item['status'] = status
            goods_item['quantity'] = product['totalInventory']
            yield goods_item
        print('================count_goods_list========handle={}===count={}'.format(handle, str(self.count_goods_list)))
        if page_info['hasNextPage']:
            self.set_has_previous_page(handle, True)
            after = edges[-1]['cursor']
            self.set_after(handle, after)
            body = self.get_request_body(handle)
            yield Request(self.API_URL, callback=self.parse_goods_list, headers=self.headers, method='POST',
                          body=body, meta=dict(handle=handle), dont_filter=True)

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
        goods_model = meta['goods_model']
        re_rule0 = r"\"Viewed Product\",(.+?)\);"
        re_info0 = re.findall(re_rule0, response.text)
        info0 = json.loads(re_info0[0])

        fabri_info = re.findall(r'attribs: {\"fabrication\":\"(.+?)\"', response.text)
        fabri = fabri_info[0] if fabri_info else ''
        select_desc = response.xpath('//meta[@name="description"]/@content')
        desc = select_desc.extract()[0] if select_desc else ''

        details = json.loads(goods_model.details)
        details['desc'] = desc
        details['fabrication'] = fabri
        product_id = info0['productId']
        price = info0['price']
        currency = info0['currency']
        price_text = price + currency
        category_name = info0['category']
        goods_item = BaseGoodsItem()
        goods_item['model'] = goods_model
        goods_item['spider_name'] = self.name
        goods_item['category_name'] = category_name
        goods_item['price_text'] = price_text
        goods_item['details'] = details
        reviews_url = 'https://api.yotpo.com/v1/widget/ohYKQnKU978xXhdov6tKkYMA1R62IqCn2kKD0aDv/products/{}/reviews.json'.format(str(product_id))
        yield Request(reviews_url, callback=self.parse_goods_reviews, meta=dict(goods_item=goods_item))

        # json_response = json.loads(response.text)
        # data = json_response['data']
        # if 'products' not in data:
        #     return False
        # edges = data['products']['edges']
        # for edge in edges:
        #     product = edge['node']
        #     attrs = self.get_nodes_by_collection(product['attributes'])
        #     fabrication = ''
        #     for attr in attrs:
        #         if attr['key'] == 'fabrication':
        #             fabrication = attr['value']

    def parse_goods_reviews(self, response: TextResponse):
        meta = response.meta
        goods_item = meta['goods_item']
        json_info = json.loads(response.text)
        status = json_info['status']
        reviews_num = 0
        average_score = 0
        if status['code'] == 200:
            bottomline = json_info['response']['bottomline']
            average_score = bottomline['average_score']
            reviews_num = bottomline['total_review']
        goods_item['reviews_num'] = reviews_num
        yield goods_item

