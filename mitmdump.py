import os
# ROOT_PATH = '/home/santic/projects/python/mitm'
# dirpath = ROOT_PATH + '/helpers'
# sys.path.append(dirpath)
# print(dirpath)
from mitmproxy import ctx
from mitmproxy.http import HTTPFlow
from pyscrapy.helpers import Logger

logger = Logger()
logger.echo_msg = True


def request(flow: HTTPFlow):
    # 篡改网络请求
    flow.request.headers["sec-ch-ua-platform"] = "Windows"
    flow.request.headers['hello3'] = 'world56'
    flow.request.headers[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    if flow.request.method == 'CONNECT':
        return
    # if flow.live:
    #     print('okkkkkkkkk')
    #     proxy = ('127.0.0.1', 1234)
    #     flow.live.change_upstream_proxy_server(proxy)

    # # 实例化输出类
    # info = ctx.log.info
    # # 打印请求的url
    # info(request.url)
    # # 打印请求方法
    # info(request.method)
    # # 打印host头
    # info(request.host)
    # # 打印请求端口
    # info(str(request.port))
    # 打印所有请求头部

    # 打印cookie头
    # info(str(request.cookies))


# 所有服务器响应的数据包都会被这个方法处理
# 所谓的处理，我们这里只是打印一下一些项
def response(flow: HTTPFlow):
    # 获取响应对象
    response = flow.response
    request = flow.request
    if request.url.startswith('https://www.amazon.com/'):
        if response.text.find('B0716H4QZ1') > -1:
            urlmsg = "SUCCESS =============================" + request.url
            conent = 'Content:' + response.text
            logger.debug(urlmsg)
            logger.debug(conent)


    # response.text = response.text.replace('百度', '摆渡')
    # print(response.headers)
    # print(response.text)
    # # 实例化输出类
    # info = ctx.log.info
    # # 打印响应码
    # info(str(response.status_code))
    # # 打印所有头部
    # info(str(response.headers))
    # # 打印cookie头部
    # info(str(response.cookies))
    # # 打印响应报文内容
    # info(str(response.text))


if __name__ == '__main__':
    # os.system()程序在前台运行，可能有阻塞。 os.popen() 程序在后台运行
    os.system("mitmdump --mode upstream:http://127.0.0.1:1080 -s mitmdump.py -p 8889")

