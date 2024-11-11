import sys
sys.path.append("..")
import os
# dirpath = '/home/santic/projects/python/mitm/helpers'
# sys.path.append(dirpath)
# print(dirpath)
# 日志输出功能（不同颜色）
from mitmproxy.http import HTTPFlow
from service.Logger import Logger
import protest, debug
logger = Logger()
logger.echo_msg = True

handlers = [protest, debug]


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


def response(flow: HTTPFlow):
    # 获取响应对象
    for h in handlers:
        h.response(flow)

    # response.text = response.text.replace('百度', '摆渡')
    # # 实例化输出类
    # info = ctx.log.info
    # info(str(response.status_code))  response.headers  response.cookies response.headers


if __name__ == '__main__':
    # 进入pyhon虚拟环境，然后执行命令: python mitm.py
    # os.system()程序在前台运行，可能有阻塞。 os.popen() 程序在后台运行
    # os.system("mitmdump -s mitmdump.py -p 8889")
    os.system("mitmdump -s mitm.py -p 8889")
    # os.system("mitmweb --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889 --upstream-cert=false")

