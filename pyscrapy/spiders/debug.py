from scrapy.http import TextResponse
from pyscrapy.spiders import BaseSpider
from scrapy import Request


# scrapy crawl debug -a sitename=4tharq
# scrapy crawl debug -a sitename=aybl
class DebugSpider(BaseSpider):
    name: str = 'debug'

    custom_settings = {
        # 'DOWNLOAD_DELAY': 1,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3, # default 8
        'CONCURRENT_REQUESTS': 6, # default 16 recommend 5-8
    }

    def __init__(self, name=None, **kwargs):
        self.allowed_domains = ['httpbin.org', 'baidu.com', '127.0.0.1', "google.com", "4tharq.com", "www.aybl.com"]
        self.base_url = "https://httpbin.org"
        self.domain = "httpbin.org"
        super(DebugSpider, self).__init__(name=name, **kwargs)
        print(f"----debug--init---kwargs({kwargs})-----")


    def start_requests(self):
        # start_url = "https://www.google.com/"
        start_url = self.get_siteurl()
        yield Request(
            start_url,
            callback=self.parse,
            # meta=dict(splash=True)
            # method='POST',
            # headers=headers
        )

    def parse(self, response: TextResponse, **kwargs):
        text = response.text
        url = response.url
        print(f'----------currenturl{url}-----')
        sitename = self.get_sitename()
        filename = f'runtime/{sitename}.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'---------response---text({text})')
        return

    def get_siteurl(self) -> str:  
        start_url = "https://httpbin.org/get"
        sitemap_url = {
            'httpbin': "https://httpbin.org/get",
            'google': 'https://www.google.com/',
            'baidu': "https://www.baidu.com/",
            "4tharq": "https://4tharq.com/collections/all",
            "aybl":"https://www.aybl.com/collections/all-products",
        }
        sitename = self.get_sitename()
        if sitename in sitemap_url:
            start_url = sitemap_url[sitename]
        else:
            errmsg = f"----debug--get_siteurl--err--sitename({sitename}) not in sitemap_url({sitemap_url})----"
            print(errmsg)
            raise Exception(errmsg)
        return start_url
    def get_sitename(self) -> str:
        return self.sitename if hasattr(self, "sitename") else "httpbin"