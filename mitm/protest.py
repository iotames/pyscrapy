from mitmproxy.http import HTTPFlow
import json

purls = []

def request(flow: HTTPFlow):
    flow.request.cookies
    flow.request.headers["sec-ch-ua-platform"] = "Windows"
    flow.request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
    if flow.request.method == 'CONNECT':
        return

def response(flow: HTTPFlow):
    response = flow.response
    request = flow.request
    if request.url.startswith("https://www.protest.eu/graphql?tweakwiseNavigation/categoryId="):
        resp = json.loads(response.text)
        items = resp['data']['tweakwiseNavigation']['items']
        f = open("protest.csv", "a", encoding="utf-8")
        f.write('Image,Code,Title,Price,ColorNum,Url\n')
        for item in items:
            # id, priceRange
            prod = item['product']
            # https://webcdn.protest.eu/resize?type=auto&stripmeta=true&url=https://www.protest.eu/media/catalog/product/1/6/1636000_408_model_front-half_01_web_1.png?quality=90&width=300
            image = prod['listImage']
            image = f"https://webcdn.protest.eu/resize?type=auto&stripmeta=true&url=https://www.protest.eu/media/catalog/product{image}?quality=72&width=300"
            code = prod['sku']
            title = prod['name']
            url_key = prod['urlKey']
            url = f"https://www.protest.eu/en/global/{url_key}"
            minprice = prod['priceRange']['minimumPrice']
            price = minprice['finalPrice']['value']
            colorsnum = len(prod['alternativeColors'])+1
            if url in purls:
                continue
            purls.append(url)
            print("------INFO------", code, title, image, url, price, colorsnum)
            msg = f"{image},{code},{title},{price},{colorsnum},{url}\n"
            f.write(msg)
        f.close()

