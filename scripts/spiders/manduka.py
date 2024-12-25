import requests
from bs4 import BeautifulSoup
import os
import csv  # 导入 csv 模块

base_url = "https://www.manduka.com"

# 目标网页 URL
url = "https://www.manduka.com/collections/yoga-clothing"

# 代理配置
proxies = {
    "http": "http://127.0.0.1:7890",  # HTTP 代理
    "https": "http://127.0.0.1:7890",  # HTTPS 代理
}

debug = True

html_content = ""
filename = "manduka_list.html"
# 判断文件是否存在
if debug and os.path.exists(filename):
    # 从文件读取HTML内容
    with open(filename, 'r', encoding='utf-8') as file:
        html_content = file.read()
else:
    # 发送 HTTP 请求获取网页内容
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
    response = requests.get(url, proxies=proxies, headers=headers)
    html_content = response.text
    # 把网页内容保存到本地文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
        print("文件保存成功")

soup = BeautifulSoup(html_content, "html.parser")
# 查找商品信息
products = soup.find_all("div", class_="product-card product-card--variant united-states")  # 根据页面结构调整 class
print("--------products len--({})------".format(len(products)))

# 初始化列表存储商品信息
product_data = []

# 遍历每个商品
for product in products:
    # 获取商品链接
    product_link = product.find("a", class_="full-unstyled-link")["href"]
    product_link = f"{base_url}{product_link}"  # 拼接完整链接

    # 获取商品标签
    tags = [tag.text.strip() for tag in product.find_all("span", class_="product-card__badge desktop-badge") if tag.text.strip()]

    # 获取商品图片地址
    image_url = "https:" + product.find("img", class_="product-card__featured-image")["src"]
    thumbnail_url = image_url.replace("width=1500", "width=300")

    # 获取商品标题
    title = product.find("p", class_="product-card__title").text.strip()

    # 获取商品颜色
    color = product.find("p", class_="product-card__color").text.strip()

    # 获取商品尺寸列表
    size_list = [size.text.strip() for size in product.find("ul", class_="product-card__sizes").find_all("li") if size.text.strip()]

    # 获取商品价格
    old_price_text = product.find("span", class_="price-item price-item--regular").text.strip()
    final_price_text = product.find("span", class_="price-item price-item--sale price-item--last").text.strip()

    data = {
        "缩略图": thumbnail_url,
        "商品标题": title,
        "颜色": color,
        "原价": old_price_text,
        "销售价": final_price_text,
        "尺码数": len(size_list),
        "尺寸列表": ", ".join(size_list),  # 将列表转换为逗号分隔的字符串
        "标签": ", ".join(tags),  # 将列表转换为逗号分隔的字符串
        "图片地址": image_url,
        "商品地址": product_link
    }
    print("---------------", data)
    # 将信息添加到列表
    product_data.append(data)

# 将数据保存为 CSV 文件
csv_filename = "manduka.csv"
with open(csv_filename, mode='w', encoding='utf-8', newline='') as file:
    # 定义 CSV 文件的列名
    fieldnames = ["缩略图", "商品标题", "颜色", "原价", "销售价", "尺码数", "尺寸列表", "标签", "图片地址", "商品地址"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    # 写入表头
    writer.writeheader()
    
    # 写入数据
    for data in product_data:
        writer.writerow(data)

print(f"商品信息已成功保存到 {csv_filename} 文件中！")