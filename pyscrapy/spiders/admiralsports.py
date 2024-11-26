from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from models import UrlRequest, UrlRequestSnapshot
from pyscrapy.items import BaseProductItem, FromPage
from urllib.parse import quote


class AdmiralsportsSpider(BaseSpider):
    name = "admiralsports"
    base_url = "https://www.admiralsports.shop"
    allowed_domains = ["www.admiralsports.shop", "payment.admiralsports.shop"]
    start_urls = ["https://www.admiralsports.shop"]

    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        # 取消 URL 长度限制
        'URLLENGTH_LIMIT': None,
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'GroupName', 'Code', 'Title', 'PriceText', 'OldPrice', 'FinalPrice', 'SkuNum', 'Image', 'Description', 'Url'],
        # 下面内容注释掉，爬虫自动导出数据到xlsx文件的功能，会默认关闭。请在命令行使用 -o 参数，指定导出的文件名。
        # 'FEED_URI': 'admiralsports.xlsx',
        # 'FEED_FORMAT': 'xlsx'
    }

    start_urls_group = [
        {'index': 604, 'title': 'andras', 'url': 'https://www.admiralsports.shop/el/andras/papoutsia.html'},
        {'index': 608, 'title': 'gynaika', 'url': 'https://www.admiralsports.shop/el/gynaika/papoutsia.html'},
        {'index': 611, 'title': 'paidi', 'url': 'https://www.admiralsports.shop/el/paidi/papoutsia.html'},
        {'index': 606, 'title': 'outlet', 'url': 'https://www.admiralsports.shop/el/outlet/papoutsia.html'},
    ]
    
    # start_urls = []
    
    def start_requests(self):
        self.page_size = 40
        for gp in self.start_urls_group:
            groupName = gp['title']
            groupIndex = gp['index']
            yield Request(self.get_list_url(1, self.page_size, groupIndex), callback=self.parse_list, meta=dict(list_url=gp['url'], page=1, step=1, group=groupIndex, GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))            

    def parse_list(self, response: TextResponse):
        meta = response.meta
        page = meta['page']
        groupName = meta['GroupName']
        self.lg.debug(f"-------parse_list--page={page}----requrl({response.url})---")

        if 'dl' in meta:
            self.lg.debug(f"----Skiped------parse_list--requrl({response.url})--page:{page}")
            dl = meta['dl']
            prods = dl['ProductList']
        else:
            result = response.json()
            total_count = result['data']['products']['total_count']
            total_page = result['data']['products']['page_info']['total_pages']
            prods = []
            for item in result['data']['products']['items']:
                dd = BaseProductItem()
                dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_LIST
                dd['GroupName'] = groupName
                dd['Title'] = item['name']
                dd['UrlKey'] = item['url_key']
                dd['Url'] = "{}/el/{}".format(self.base_url, dd['UrlKey'])
                dd['Code'] = item['sku']
                dd['Image'] = item['image']['url']
                dd['Thumbnail'] = item['image']['url'] + "&width=200"
                dd['image_urls'] = [dd['Thumbnail']]
                dd['Description'] = item['short_description']['html']
                priceinfo = item['price_range']['minimum_price']['final_price']
                dd['PriceText'] = str(priceinfo['value']) + priceinfo['currency'] # ['regularPrice']['value']
                dd['FinalPrice'] = priceinfo['value']
                dd['OldPrice'] = item['price_range']['minimum_price']['regular_price']['value']
                dd['SkuNum'] = len(item['variants'])
                prod = {}
                for key, value in dd.items():
                    prod[key] = value
                prods.append(prod)
            nextPageUrl = ""
            if page < total_page:
                nextPageUrl = self.get_list_url(page+1, self.page_size, meta['group'])
            dl = {'TotalCount': total_count, 'TotalPage': total_page, 'Url': meta['list_url'], 'PageIndex': page, 'NextPageUrl': nextPageUrl, 'FromKey':FromPage.FROM_PAGE_PRODUCT_LIST, 'ProductList': prods}
            ur: UrlRequest = meta['UrlRequest']
            ur.setDataFormat(dl)
            ur.setDataRaw(response.text)
            ur.saveUrlRequest(meta['StartAt'])
            UrlRequestSnapshot.create_url_request_snapshot(ur, meta['StartAt'], ur.status_code)
        for dd in prods:
            yield dd
            # dd['FromKey'] = FromPage.FROM_PAGE_PRODUCT_DETAIL
            # yield Request(dd['Url'], self.parse_detail, meta=dict(dd=dd, page=page, step=0, group=meta['group'], FromKey=FromPage.FROM_PAGE_PRODUCT_DETAIL))
        # self.lg.debug(f"-----parse_list-next_page({page+1})-{dl['NextPageUrl']}---")
        if dl['NextPageUrl'] != "":
            self.lg.debug(f"-----parse_list--goto--next_page({dl['PageIndex']+1}/{dl['TotalPage']})--")
            yield Request(dl['NextPageUrl'], callback=self.parse_list, meta=dict(list_url=meta['list_url'], page=page+1, step=meta['step'], group=meta['group'], GroupName=groupName, FromKey=FromPage.FROM_PAGE_PRODUCT_LIST))

    # def parse_detail(self, response: TextResponse):
      
    #     meta = response.meta
    #     dd = meta['dd']
    #     if 'SkipRequest' in dd:
    #         # self.lg.debug(f"----Skiped----typedd({type(dd)})---parse_detail--requrl:{response.url}---dd:{dd}-")
    #         yield dd
    #     else:
    #         # TODO
            
    #         self.lg.debug(f"------parse_detail--yield--dd--to--SAVE--requrl:{response.url}----dd:{dd}-")
    #         yield dd

    def get_list_url(self, page_index: int, page_size: int, category_id: int) -> str:
        # 定义模板字符串
        template = """
{            products(        filter: {            category_id: {eq: "{category_id}"}                    }        sort: { position: ASC }     pageSize:{page_size}    currentPage:{current_page}         ){        total_count        aggregations{            attribute_code            label            count            options{                label                value                count            }        }        sort_fields {            default            options {              label              value            }        }        page_info{            total_pages          }        items{                    id        uid        name        url_key        short_description {            html        }        only_x_left_in_stock        type:__typename        review_count        rating_summary         special_price        stock_status        sku        meta_description        meta_title        meta_keyword        image {            disabled            label            position            url        }        media_gallery {            disabled            label            position            url        }         url_rewrites  {            parameters  {              name              value            }            url        }        mobiSimpleProductOptions        mobiConfigurableProductOptions        product_price_range                            }    }    }
"""
        # 使用字符串格式化替换变量
        querystr = template.strip().replace("{category_id}", str(category_id)).replace("{page_size}", str(page_size)).replace("{current_page}", str(page_index))
        return "https://payment.admiralsports.shop/graphql/?query={}".format(quote(querystr))
