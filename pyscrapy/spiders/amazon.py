from scrapy.exceptions import UsageError
from scrapy import Request
from pyscrapy.spiders.basespider import BaseSpider
from urllib.parse import urlencode
from Config import Config
from pyscrapy.grabs.amazon_goods_list import GoodsRankingList, GoodsListInStore
from pyscrapy.grabs.amazon_goods import AmazonGoodsDetail
from pyscrapy.grabs.amazon_goods_reviews import AmazonGoodsReviews
from pyscrapy.extracts.amazon import Common as XAmazon, GoodsReviews as XGoodsReviews
from pyscrapy.models import SiteMerchant
from pyscrapy.items import AmazonGoodsItem


class AmazonSpider(BaseSpider):

    name = 'amazon'
    base_url = XAmazon.BASE_URL

    # handle_httpstatus_list = [404]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'IMAGES_STORE': Config.ROOT_PATH + "/runtime/images",
        'COMPONENTS_NAME_LIST_DENY': [],
        'SELENIUM_ENABLED': False
    }

    url_params = {
        "language": 'zh_CN'
    }

    top_goods_urls = [
        # '/Best-Sellers-Womens-Activewear-Skirts-Skorts/zgbs/fashion/23575633011?{}'
        '/bestsellers/fashion/10208103011?{}'  # 骑行短裤
        # '/bestsellers/sporting-goods/706814011?{}'  # 户外休闲销售排行榜
    ]

    stores_urls = [
        {'store_name': 'Baleaf', 'urls': ['/stores/page/105CBE98-4967-4033-8601-F8B84867E767']},
        # {'store_name': 'sponeed', 'urls': [
        # 7个网页中6个有反爬。 需要从XHR网络请求中抓取ASINList
        #     '/stores/page/FB3810D0-2453-447E-86C3-45C094E7F3A0',
        #     '/stores/page/65B90D63-5A93-422C-81F5-CD4297B1B65D',
        #     '/stores/page/20758B24-570B-4AB8-B53E-6FD5DC9E8514',
        #     '/stores/page/F36A4167-83B4-45CE-8C08-4F176153083D',
        #     '/stores/page/FBBC92DD-D089-4156-899F-45B69C58F989',
        #     '/stores/page/531253C5-D835-4521-8526-A0DAC4EF4C89',
        #     '/stores/page/258CD320-5D69-43A6-B30D-06F1AFA70C4D'
        # ]}

    ]

    asin_list = []

    CHILD_GOODS_LIST_STORE_PAGE = 'goods_list_store_page'
    CHILD_GOODS_LIST_RANKING = 'goods_list_ranking'
    CHILD_GOODS_REVIEWS = 'goods_reviews'
    CHILD_GOODS_LIST_ASIN = 'goods_list_asin'

    goods_model_list: list

    def __init__(self, name=None, **kwargs):
        super(AmazonSpider, self).__init__(name=name, **kwargs)
        if 'spider_child' not in kwargs:
            msg = 'lost param spider_child'
            raise UsageError(msg)
        self.spider_child = kwargs['spider_child']

    def start_requests(self):
        if self.spider_child == self.CHILD_GOODS_LIST_STORE_PAGE:
            for store in self.stores_urls:
                store_name = store['store_name']
                store_find = {'name': store_name, 'site_id': self.site_id}
                print(store_find)
                store_model = self.db_session.query(SiteMerchant).filter_by(**store_find).first()
                if not store_model:
                    store_model = SiteMerchant(**store_find)
                    self.db_session.add(store_model)
                    self.db_session.commit()
                for url in store['urls']:
                    yield Request(
                        self.get_site_url(url),
                        callback=GoodsListInStore.parse,
                        meta=dict(merchant_id=store_model.id)
                    )
        if self.spider_child == self.CHILD_GOODS_LIST_RANKING:
            for url in self.top_goods_urls:
                self.url_params['pg'] = "1"
                url = self.base_url + url.format(urlencode(self.url_params))
                yield Request(
                    url,
                    callback=GoodsRankingList.parse,
                    headers=dict(referer=self.base_url),
                    meta=dict(page=1)
                )
        if self.spider_child == self.CHILD_GOODS_REVIEWS:
            asin = "B08Q82QYSV"
            goods_url = XAmazon.get_url_by_code(asin, self.url_params)
            reviews_url = XGoodsReviews.get_reviews_url_by_asin(asin)
            next_request = Request(
                reviews_url,
                callback=AmazonGoodsReviews.parse,
                headers=dict(referer=goods_url),
                meta=dict(goods_code=asin)  # goods_id=goods_id
            )
            yield Request(
                goods_url,
                callback=AmazonGoodsDetail.parse,
                headers=dict(referer=self.base_url),
                meta=dict(next_request=next_request)
            )
        if self.spider_child == self.CHILD_GOODS_LIST_ASIN:
            store_name = 'sponeed'
            store_find = {'name': store_name, 'site_id': self.site_id}
            store_model = self.db_session.query(SiteMerchant).filter_by(**store_find).first()
            merchant_id = store_model.id
            # 手动填写 asin_list [ASIN列表通过mitmproxy中间代理人抓取, 注意缓存后可能会不再走网络请求而是直接读取缓存]
            self.asin_list = [
                {
                    'tag': 'SPECIAL',
                    'items': ["B0716H4QZ1", "B010D2OP2S", "B086HJFHYL", "B00YGVE0D2", "B074THHVVQ", "B07FL3XHSV", "B01CUFV66Y", "B014NTMLEQ", "B073Y87NYX", "B01N5GG0TX", "B0746GTZBR", "B07DZ8JV77", "B01M73S4C2", "B0761Q1TC1", "B00VLM2S10", "B075ZVSRFM", "B016XJ4BEC", "B01914PO0Q", "B013FG08PM", "B013FFYXOK", "B07B2PTZL7", "B01DOUVF38", "B07L2NLQDG", "B016DHQYQM", "B08KZBN54R", "B0166QTA5C", "B00VSYV772", "B07GPD6TCT"],
                },
                {
                    'tag': 'NEW ARRIVAL',
                    'items': ["B08LV4C4FM", "B08XJY5JTX", "B08LV3NJCF", "B08ZDDHFGP", "B0932ZZKZS", "B094ZSF3FJ", "B086H1ZCR7", "B086HJLQ3K", "B08KZBN54R", "B014L0N82Q"],
                },
                {
                    'tag': 'CYCLING BOTTOM',
                    'items': ["B0716H4QZ1", "B079FM844N", "B00VSYV90W", "B08LV4C4FM", "B07B8DY3QL", "B072P5P8XW", "B06XRCQ3N8", "B083FG5PNZ", "B074JC8VFW", "B00YGVDFAQ", "B073Y87NYX", "B07DZ8JV77", "B07DZB7C91", "B085C6FNJ6", "B08XJY5JTX", "B085C6NLGC", "B00YGVD9I4", "B00YGVDM72", "B00VSYV772", "B00YGVE0D2", "B01AVTZV6C", "B016XJ4FW0", "B06XK457Z6", "B00YGVD2EA"],
                },
                {
                    'tag': 'SHORT SLEEVE',
                    'items': ["B08C9XVK96", "B08CGHP5HL", "B086H1ZCR7", "B07PPYWBNL", "B08ZDFH8CF", "B08CH1B8WD", "B01N6HWJ9X", "B00VLM36Q6", "B016XJ4BEC", "B074THHVVQ", "B074TFXW8L", "B00WI0B2BQ", "B00WI0BEUU", "B00VLM2QVC", "B00VLM3ASU", "B074DT2BVQ", "B01CUFV78G", "B01DOUVF38", "B0140XU7XM", "B00SD1S3ZC", "B00VK9AU2S", "B013FFZ8SK", "B014NZMUDW", "B013FPOIO0", "B013FPOHDW", "B0140XU778", "B011FRBIZM", "B015MHG8XI", "B0746H9652", "B01LZ0GJ7B", "B07C97LHSS", "B010D2OP2S", "B07FL56P53", "B07V8S8845", "B086HJLQ3K", "B07B2PB8SH", "B07B2PTZL7", "B016XJ48PO", "B07GPGGR68", "B07GPD25XQ"],
                },
                {
                    'tag': 'LONG SLEEVE',
                    'items': ["B074JCKM8F", "B01M7QD5RF", "B0154I4VSY", "B01914POVA", "B01N5DL5TY", "B014L0N82Q", "B01M2C4VJF", "B01M2BIPKE", "B0166QTA8O", "B014L0MYTY", "B075ZT3R3R", "B07ZCM6521", "B07HD4ZG47", "B07YV8JKM8", "B075ZVNRCZ", "B00VLM2S10", "B07HD4ZS6H", "B07YV955QV", "B07L2NXKPF", "B077G7NLWY", "B07YV2JBD8", "B01LC1BXME", "B0761Q1TC1", "B013FG08PM", "B0166QTA5C", "B08KZNPTBR", "B08KZBN54R", "B07YV99WGX", "B07YV9DPQY", "B075ZV7HX9", "B075T7YC88", "B01MS3KBIA", "B016DHQYQM", "B018R1M96G", "B013FFYXOK", "B013FFZ4A2", "B01A8UEKHU", "B013FFZJ84", "B019AS5HZ0"],
                },
                {
                    'tag': 'WOMEN\'S CYCLING',
                    'items': ["B013FFYXOK", "B013FG08PM", "B013FFZ4A2", "B01A8UEKHU", "B00VK9AU2S", "B013FFZ8SK", "B013FFZJ84", "B013FG0456"],
                }
            ]
            # self.asin_list = [self.asin_list[-1]]
            for group in self.asin_list:
                category_name = group['tag']
                for asin in group['items']:
                    item = AmazonGoodsItem()
                    item['merchant_id'] = merchant_id
                    item['asin'] = asin
                    item['code'] = asin
                    item['category_name'] = category_name
                    yield Request(
                        XAmazon.get_url_by_code(asin, self.url_params),
                        callback=AmazonGoodsDetail.parse,
                        # dont_filter=True,
                        meta=dict(item=item)
                    )



