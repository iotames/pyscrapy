from pyscrapy.items import  BaseProductItem, FromPage
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

    # process_item: 管道中专门处理Item数据的方法。必须返回Item对象，数据才能被下游管道捕获。
    def process_item(self, item: BaseProductItem, spider: BaseSpider):
        # print('========dbpipeline==ProductDetail===process_item=', spider.name, item)        
        if 'FromKey' not in item:
            raise RuntimeError('======item key: FromKey is empty==')
        if item['FromKey'] == FromPage.FROM_PAGE_PRODUCT_LIST:
            return item
        if 'UrlRequest' not in item:
            errmsg = f"-----item key: UrlRequest is empty--FromKey({item['FromKey']})---requrl({item['Url']})---"
            lg.debug(errmsg)
            raise RuntimeError(errmsg)
        if 'SkipRequest' in item:
            print("---------Skip--Save----urlRequest---ProductDetail----SkipRequest:", item['SkipRequest'])
            return item

        checkSpider(spider)
        dataFormat = {}
        
        for key, value in item.items():
            if key in BaseProductItem.NOT_SAVE_FILEDS:
                continue
            dataFormat[key] = value
            
        urlRequest: UrlRequest = item['UrlRequest']
        dataRaw = item.get('DataRaw', None)
        if dataRaw is not None:
            urlRequest.setDataRaw(dataRaw)
        urlRequest.setDataFormat(dataFormat)
        urlRequest.site_id = spider.site_id
        urlRequest.saveUrlRequest(item['StartAt'])
        UrlRequestSnapshot.create_url_request_snapshot(urlRequest, item['StartAt'], urlRequest.status_code)
        return item