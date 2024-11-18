from pyscrapy.items import  BaseProductItem
from pyscrapy.spiders import BaseSpider
from models import UrlRequest, UrlRequestSnapshot
from datetime import datetime
from copy import copy
from service import DB, Logger
from sqlalchemy.orm.session import Session
from pyscrapy.spiders import BaseSpider
import json


def checkSpider(spider: BaseSpider):
        if not spider.name or len(spider.name.strip()) == 0:
            err_msg = 'process_item error: spider.name is empty!'
            print(err_msg)
            raise RuntimeError(err_msg)

class Base:

    # __db_session: Session
    def __init__(self):
        db = DB.get_instance()
        self.__db_session = db.get_db_session()

    @property
    def db_session(self)-> Session:
        # 因为 Python 的名称修饰（Name Mangling）机制，不加这个修饰器会报错：
        # AttributeError: 'ProductDetail' object has no attribute '_ProductDetail__db_session'
        return self.__db_session


lg = Logger.get_instance()

class ProductDetail(Base):

    def process_item(self, item: BaseProductItem, spider: BaseSpider):
        # print('========dbpipeline==ProductDetail===process_item=', spider.name, item)
        if 'FromKey' not in item:
            raise RuntimeError('======item key: FromKey is empty==')
        if 'UrlRequest' not in item:
            errmsg = f"-----item key: UrlRequest is empty--FromKey({item['FromKey']})---requrl({item['Url']})---"
            lg.debug(errmsg)
            raise RuntimeError(errmsg)
        if 'SkipRequest' in item:
            print("---------Skip--Save----urlRequest---ProductDetail----SkipRequest:", item['SkipRequest'])
            return

        checkSpider(spider)
        not_update = ['image_urls', 'image_paths', 'UrlRequest', 'FromKey', 'SkipRequest', 'StartAt']
        
        dataFormat = {}
        
        for key, value in item.items():
            if key in not_update:
                continue
            dataFormat[key] = value
            
        urlRequest: UrlRequest = item['UrlRequest']
        urlRequest.setDataFormat(dataFormat)
        urlRequest.site_id = spider.site_id
        urlRequest.saveUrlRequest(item['StartAt'])
        UrlRequestSnapshot.create_url_request_snapshot(urlRequest, item['StartAt'], urlRequest.status_code)


# {'Category': 'Leggings',
#  'Color': 'Slate',
#  'FinalPrice': '48',
#  'Material': '83% Nylon 17% Spandex',
#  'OldPrice': '48',
#  'OldPriceText': '€48',
#  'PriceText': '€48',
#  'SizeList': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
#  'SizeNum': 6,
#  'Thumbnail': 'https://4tharq.com/cdn/shop/files/peyt-slate-L_BM_F1.jpg?v=1699913791&width=533',
#  'Title': 'PEYTON Leggings',
#  'TotalInventoryQuantity': 764,
#  'Url': 'https://4tharq.com/products/peyton-leggings-slate',
#  'image_urls': ['https://4tharq.com/cdn/shop/files/peyt-slate-L_BM_F1.jpg?v=1699913791&width=533'],
#  'spider_name': '4tharq'}