import json
import os
# ROOT_PATH = '/home/santic/projects/python/mitm'
# dirpath = ROOT_PATH + '/helpers'
# sys.path.append(dirpath)
# print(dirpath)
# 日志输出功能（不同颜色）
from mitmproxy import ctx
from mitmproxy.http import HTTPFlow
from pyscrapy.helpers import Logger
from pyscrapy.extracts.amazon import GoodsListInStore
logger = Logger()
logger.echo_msg = True


def request(flow: HTTPFlow):
    # 篡改网络请求
    flow.request.headers["sec-ch-ua-platform"] = "Windows"
    # flow.request.headers['hello3'] = 'world56'
    flow.request.headers[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
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
    if request.url.startswith('https://www.amazon.com/'):
        if response.text.find("\"content\":{\"ASINList\":") > -1:
            urlmsg = "SUCCESS =============================" + request.url
            asin_list = GoodsListInStore.get_asin_list(response.text)
            logger.debug(urlmsg + os.linesep + json.dumps(asin_list))

    if response.text.find('2034') > -1:
        urlmsg = "SUCCESS =============================" + request.url
        logger.debug(urlmsg + os.linesep + request.text)
        logger.debug(response.text)

    # response.text = response.text.replace('百度', '摆渡')
    # # 实例化输出类
    # info = ctx.log.info
    # info(str(response.status_code))  response.headers  response.cookies response.headers


if __name__ == '__main__':
    # os.system()程序在前台运行，可能有阻塞。 os.popen() 程序在后台运行
    os.system("mitmdump --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889")
    # os.system("mitmweb --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889")

