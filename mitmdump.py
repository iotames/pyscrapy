import json
import os
from xml import dom
# ROOT_PATH = '/home/santic/projects/python/mitm'
# dirpath = ROOT_PATH + '/helpers'
# sys.path.append(dirpath)
# print(dirpath)
# 日志输出功能（不同颜色）
from mitmproxy import ctx
from mitmproxy.http import HTTPFlow
from pyscrapy.helpers import Logger, JsonFile
from pyscrapy.extracts.amazon import GoodsListInStore
logger = Logger()
logger.echo_msg = True


def request(flow: HTTPFlow):
    flow.request.cookies
    # 篡改网络请求
    domain = "app.dnbhoovers.com"
    if flow.request.url.find(domain) > -1:
        cookie_file = f"{domain}.cookie"
        dnb_cookie = ""
        with open(cookie_file, "r", encoding="utf-8") as file:
            dnb_cookie = file.read()
        # logger.debug(f"-----------dnbhoovers_cookie=({dnb_cookie})")
        flow.request.headers["cookie"] = dnb_cookie
    flow.request.headers["sec-ch-ua-platform"] = "Windows"
    # flow.request.headers['hello3'] = 'world56'
    flow.request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
    if flow.request.method == 'CONNECT':
        return
    # if flow.live:
    #     print('okkkkkkkkk')
    #     proxy = ('127.0.0.1', 1234)
    #     flow.live.change_upstream_proxy_server(proxy)

    # log = ctx.log
    # log.info(request.url)
    # log.warn(request.method)
    # log.error(request.host)
    # info(str(request.port))
    # 打印cookie头
    # info(str(request.cookies))


def response(flow: HTTPFlow):
    # 获取响应对象
    response = flow.response
    request = flow.request
    if request.url.find("app.dnbhoovers.com") > -1:
        response.text = response.text.replace("<a href=\"/logout\">登出</a>", "")
    if request.url.startswith('https://www.amazon.com/'):
        if response.text.find("\"content\":{\"ASINList\":") > -1:
            urlmsg = "SUCCESS =============================" + request.url
            asin_list = GoodsListInStore.get_asin_list(response.text)
            logger.debug(urlmsg + os.linesep + json.dumps(asin_list))
    if request.url.startswith("https://4fstore.com/graphql"):
        if response.text.find("Main fabric") > -1:
            logger.debug("------find--Main fabric---:"+request.url)

    # response.text = response.text.replace('百度', '摆渡')
    # # 实例化输出类
    # info = ctx.log.info
    # info(str(response.status_code))  response.headers  response.cookies response.headers


if __name__ == '__main__':
    # os.system()程序在前台运行，可能有阻塞。 os.popen() 程序在后台运行
    os.system("mitmdump -s mitmdump.py -p 8889")
    # os.system("mitmdump --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889 --upstream_cert=false")
    # os.system("mitmweb --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889")

