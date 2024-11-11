import sys
sys.path.append("..")
from mitmproxy.http import HTTPFlow
from service.Logger import Logger
logger = Logger()
logger.echo_msg = True

def request(flow: HTTPFlow):
    flow.request.cookies
    flow.request.headers["sec-ch-ua-platform"] = "Windows"
    flow.request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
    if flow.request.method == 'CONNECT':
        return

def response(flow: HTTPFlow):
    response = flow.response
    request = flow.request
    # https://byltbasics.com/products/drop-cut-lux-dotted-polo?variant=39292385230950
    # https://byltbasics.com/products/kinetic-cargo-shorts?variant=39609118031974
    # https://byltbasics.com/products/henley-drop-cut-long-sleeves?variant=32001989214310
    # if response.text.find("/products/airessentials-striped-track-jacket") > -1:
    #     logger.debug("---------------Find------(/products/airessentials-striped-track-jacket)------------" + request.url)
    # if response.text.find("/products/longline-medium-impact-sports-bra") > -1:
    #     logger.debug("---------------Find-----(/products/longline-medium-impact-sports-bra)-------------" + request.url)
    if response.text.find("spanx-on-the-move-cropped-wide-leg-pant") > -1:
        logger.debug("------Find---(spanx-on-the-move-cropped-wide-leg-pant)----" + request.url)
    if response.text.find("/products/pique-shaping-swim-plunge-one-piece") > -1:
        logger.debug("-----Find--(/products/pique-shaping-swim-plunge-one-piece)---"+ request.url)
