from models import UrlRequest
from datetime import datetime
from datetime import datetime, timedelta
from scrapy.http import HtmlResponse
from pyscrapy.items import FromPage


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
        print("----------DbMiddleware--process_request-------ur---", request.meta['FromKey'], ur)

        # step, start(page), group: int
        
        mustin = ['step', 'page', 'group', 'FromKey']
        for k in mustin:
            if k not in request.meta:
                raise ValueError(f'meta must have key:{k}')
        
        if ur and ur.id > 0:
            request.meta['UrlRequest'] = ur
            # 如果最近8小时内已发送过相同的请求，则从数据库读取
            if ur.collected_at > datetime.now() - timedelta(minutes=8):
                # 看已有的数据。不再发送请求
                d = ur.data_format
                if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_LIST:
                    request.meta['dl'] = d
                    if 'ProductList' not in d:
                        raise ValueError('ProductList not in data_format')
                if request.meta['FromKey'] == FromPage.FROM_PAGE_PRODUCT_DETAIL:
                    request.meta['dd'] = d
                request.meta['SkipReqeust'] = True
                request.meta['StartAt'] = datetime.now()
                return HtmlResponse(url=request.url, body=ur.data_raw, encoding='utf-8', request=request)
            else:
                request.meta['UrlRequest'] = ur
                return None
        else:
            request.meta['UrlRequest'] = UrlRequest.createUrlRequest(request, spider.site_id, request.meta['step'], request.meta['page'], request.meta['group'])
            return None
    
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response