from models import UrlRequest
import time
from datetime import datetime, timedelta
from scrapy.http import HtmlResponse


class DbMiddleware:

    def process_request(self, request, spider):
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        
        meta = request.meta
        # 使用 request.url 和 request.body 的组合作为缓存的键
        ur = UrlRequest.getByRequest(request)
        if ur.id > 0:
            dd = ur.data_format
            dd['UrlRequest'] = ur
            meta['dd'] = dd
            meta['UrlRequest'] = ur
            # 如果最近8小时内已发送过相同的请求，则从数据库读取
            if ur.collected_at > datetime.now() - timedelta(minutes=8):
                # 看已有的数据。不再发送请求
                return HtmlResponse(url=request.url, body=ur.data_raw, encoding='utf-8', meta=meta)
            else:
                request.meta['dd'] = dd
                request.meta['UrlRequest'] = ur
                return request
        else:
            # ur = UrlRequest.createUrlRequest(request, spider.site_id, 1, 0, 0)
            # dd = {}
            # dd['UrlRequest'] = ur
            # request.meta['dd'] = dd
            request.meta['UrlRequest'] = None
            return request
    
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response