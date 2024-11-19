# Scrapy settings for pyscrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from service import Config, DB, Logger

# 初始化全局调用的单例服务
cf = Config.get_instance(os.getenv("ROOT_PATH", os.path.dirname(os.path.dirname(__file__))))
DB.get_instance(Config.get_database())
Logger.get_instance(os.path.join(cf.get_root_path(), "runtime", "logs"))

# print(Config.get_instance().get_root_path())
# print(DB.get_instance().get_db_engine_uri())
# print(Config.get_instance().get_http_proxy())

BOT_NAME = 'pyscrapy'

SPIDER_MODULES = ['pyscrapy.spiders']
NEWSPIDER_MODULE = 'pyscrapy.spiders'

# LOG_LEVEL = 'INFO' # default: DEBUG
# LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
# LOG_FILE = f'{cf.get_root_path()}/runtime/logs/scrapy.log'

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"

# Obey robots.txt rules. Default True
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'pyscrapy.dbmiddleware.DbMiddleware': 530,
    'pyscrapy.middlewares.PyscrapyDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # 'pyscrapy.pipelines.ImagePipeline': 200,
   'pyscrapy.dbpipeline.ProductDetail': 300,
}

FEED_EXPORTERS_BASE = {
    "xlsx": "pyscrapy.exportpipeline.XlsxExporter",
    "csv": "scrapy.exporters.CsvItemExporter",
}

FEED_EXPORT_FIELDS = [
    'Thumbnail', 'Category', 'Title',  'Color', 'OldPriceText', 'PriceText', 'OldPrice', 'FinalPrice', 'SizeList', 'SizeNum', 'TotalInventoryQuantity', 'Material', 'Url'
]

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
IMAGES_STORE = cf.get_images_path()
if IMAGES_STORE == "":
    raise ValueError("IMAGES_PATH is empty")