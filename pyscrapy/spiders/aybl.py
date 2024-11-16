from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request
from pyscrapy.items import BaseProductItem, FromPage
import json
import re

class AyblSpider(BaseSpider):
    name = "aybl"
    base_url = "https://www.aybl.com"
    allowed_domains = ["www.aybl.com"]
    start_urls = ["https://www.aybl.com/collections/all-products"]


    # 该属性cls静态调用 无法继承覆盖
    custom_settings = {
        'DOWNLOAD_DELAY': 1.2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'COOKIES_ENABLED': False,
        'CONCURRENT_REQUESTS_PER_IP': 5,  # default 8
        'CONCURRENT_REQUESTS': 5,  # default 16 recommend 5-8
        'FEED_URI': 'aybl.csv',
        'FEED_FORMAT': 'csv',
        'FEED_EXPORT_FIELDS': ['Thumbnail', 'Category', 'Title',  'Color', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url']
    }

