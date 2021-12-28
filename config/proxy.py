"""
IP代理池
"""
from config.baseconfig import BaseConfig
import requests


class HttpProxy(BaseConfig):

    name = 'http_proxy'
    
    # def __init__(self):
    #     super(HttpProxy, self).__init__()
    
    TYPE_VPN = 'vpn'
    TYPE_IP_POOL = 'ip_pool'

    # 收取github的2个开源IP代理池项目
    SERVICE_CUIQINGCAI = 'cuiqingcai'  # https://github.com/Python3WebSpider/ProxyPool
    SERVICE_JHAO104 = 'jhao104'  # https://github.com/jhao104/proxy_pool
    SERVICE_MAP = {
        SERVICE_CUIQINGCAI: {'base_url': 'http://127.0.0.1:5555', 'api_get': '/random'},
        SERVICE_JHAO104: {'base_url': 'http://127.0.0.1:5010', 'api_get': '/get/?type=https', 'api_delete': '/delete/'}
    }
    IP_POOL_SERVICE = SERVICE_JHAO104

    DEFAULT_CONFIG = {
        'proxy_type': TYPE_VPN,
        'ip_pool_service': SERVICE_JHAO104,
        'items': ['http://127.0.0.1:1080']
    }

    SAMPLE_CONFIG = {
        'ip_pool_service': SERVICE_JHAO104,
        'items': [
            'http://127.0.0.1:1080',
            'http://127.0.0.1:1234'
        ]
    }

    def get_proxy_from_pool(self, service: str):
        func_map = {
            self.SERVICE_CUIQINGCAI: self.get_proxy_cuiqingcai,
            self.SERVICE_JHAO104: self.get_proxy_jhao104
        }
        return func_map[service]()

    def get_proxy_cuiqingcai(self):
        service = self.SERVICE_MAP[self.SERVICE_CUIQINGCAI]
        url = service['base_url'] + service['api_get']
        return 'http://{}'.format(requests.get(url).text.strip())

    proxy = ""

    def delete_proxy(self):
        if self.config['proxy_type'] == self.TYPE_VPN:
            msg = "TYPE_VPN not suppose delete_proxy"
            print(msg)
            return False
        if self.config['ip_pool_service'] != self.SERVICE_JHAO104:
            msg = "SERVICE_CUIQINGCAI not suppose delete_proxy"
            print(msg)
            return False
        service = self.SERVICE_MAP[self.SERVICE_JHAO104]
        url = service['base_url'] + service['api_delete']
        delete_url = url + "?proxy={}".format(self.proxy)
        print("delete_proxy: " + delete_url)
        requests.get(delete_url)

    def get_proxy_jhao104(self):
        service = self.SERVICE_MAP[self.SERVICE_JHAO104]
        url = service['base_url'] + service['api_get']
        print("get_proxy_jhao104: " + url)
        proxy = requests.get(url).json().get('proxy')
        self.proxy = proxy
        http_proxy = "http://{}".format(proxy)
        print("set proxy=" + http_proxy)
        return http_proxy

    def choice_one_from_items(self):
        def get_proxy_by_pool():
            ip_pool_service = self.config['ip_pool_service']
            return self.get_proxy_from_pool(ip_pool_service)
        method_map = {
            self.TYPE_VPN: super().choice_one_from_items,
            self.TYPE_IP_POOL: get_proxy_by_pool
        }
        return method_map[self.config['proxy_type']]()

    def test_request(self, url='http://httpbin.org/get'):
        http_proxy = self.choice_one_from_items()
        proxies = {'http': http_proxy}
        print(proxies)
        return requests.get(url, proxies=proxies)


if __name__ == '__main__':
    hproxy = HttpProxy()
    print(hproxy.test_request().text)
