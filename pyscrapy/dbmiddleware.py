from models import UrlRequest
from datetime import datetime
from datetime import datetime, timedelta
from scrapy.http import HtmlResponse
from pyscrapy.items import FromPage, BaseProductItem
from service import Logger

lg = Logger.get_instance()

class DbMiddleware:

    def process_request(self, request, spider):
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        
        request.meta['StartAt'] = datetime.now()
        # 使用 request.url 和 request.body 的组合作为缓存的键
        ur = UrlRequest.getByRequest(request)
        
        lg.debug(f"-----DbMiddleware--process_request--FromKey({request.meta['FromKey']})--requrl:{request.url}--ur({ur})--request.meta:{request.meta}")

        mustin = ['step', 'page', 'group', 'FromKey']
        for k in mustin:
            if k not in request.meta:
                raise ValueError(f'meta must have key:{k}')
        
        if ur and ur.id > 0:
            request.meta['UrlRequest'] = ur
            d = ur.data_format
            d['FromKey'] = request.meta['FromKey']
            d['UrlRequest'] = request.meta['UrlRequest']
            if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_LIST:
                request.meta['dl'] = d
                if 'ProductList' not in d:
                    raise ValueError('ProductList not in data_format')
            if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_DETAIL:
                # TODO 直接从数据库赋值，可能丢失从 FROM_PAGE_PRODUCT_LIST 页面带过来的数据
                request.meta['dd'] = BaseProductItem(d)
                request.meta['dd']['StartAt'] = request.meta['StartAt']

            # 如果最近8小时内已发送过相同的请求，则从数据库读取
            if ur.collected_at > datetime.now() - timedelta(hours=8):
                # 看已有的数据。不再发送请求
                if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_DETAIL:
                    request.meta['dd']['SkipRequest'] = True
                lg.debug(f'---------skip---DbMiddleware--process_request--requrl:{request.url}-----data_format:{d}')
                return HtmlResponse(url=request.url, body=ur.data_raw, encoding='utf-8', request=request)
            lg.debug(f'-----last_collectedat > 8hours---DbMiddleware--process_request--requrl:{request.url}---')
            return None
        else:
            request.meta['UrlRequest'] = UrlRequest.createUrlRequest(request, spider.site_id, request.meta['step'], request.meta['page'], request.meta['group'])
            lg.debug(f'-------Request---DbMiddleware--process_request--requrl:{request.url}-----request.meta:{request.meta}')
            if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_DETAIL:
                request.meta['dd']['UrlRequest'] = request.meta['UrlRequest']
                request.meta['dd']['StartAt'] = request.meta['StartAt']
            return None
    
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response