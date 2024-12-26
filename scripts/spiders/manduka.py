import requests
from lxml import etree
import csv

class Manduka:
    name = "manduka"
    base_url = "https://www.manduka.com"
    # 代理配置
    proxies = {
        "http": "http://127.0.0.1:7890",  # HTTP 代理
        "https": "http://127.0.0.1:7890",  # HTTPS 代理
    }
    request_url_list = []

    def run(self):
        # 目标网页 URL
        requrls = [
            "https://www.manduka.com/collections/yoga-clothing",
            "https://www.manduka.com/collections/yoga-mats",
            "https://www.manduka.com/collections/yoga-towels",
            "https://www.manduka.com/collections/yoga-props-accessories",
            "https://www.manduka.com/collections/yoga-kits",
            "https://www.manduka.com/collections/sale-all-yoga-products",
            "https://www.manduka.com/collections/new-arrivals",
        ]

        # 将数据保存为 CSV 文件
        csv_filename = "manduka.csv"
        with open(csv_filename, mode='w', encoding='utf-8', newline='') as file:
            # 定义 CSV 文件的列名
            fieldnames = ["缩略图", "分组", "品类", "商品标题", "颜色", "价格", "原价", "销售价", "评论数", "尺码数", "尺寸列表", "标签", "面料信息", "图片地址", "商品地址"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            # 写入表头
            writer.writeheader()
            # 写入数据

            for requrl in requrls:
                html_content = self.request_url(requrl)
                if html_content == "":
                    continue
                for ctxdata in self.parse_list(html_content):
                    urlsplit = requrl.split('/')
                    groupname = ""
                    if len(urlsplit) > 1:
                        groupname = urlsplit[len(urlsplit)-1]
                    ctxdata['分组'] = groupname
                    detail_html = self.request_url(ctxdata['商品地址'])
                    if detail_html == "":
                        continue
                    data = self.parse_detail(detail_html, ctxdata)
                    writer.writerow(data)
                    print("------product--data({})-----".format(data))
        print(f"商品信息已成功保存到 {csv_filename} 文件中！")

    def parse_detail(self, bstr: str, ctxdata: dict) -> dict:
        # 使用 lxml 解析 HTML
        html = etree.HTML(bstr)
        ctxdata['评论数'] = 0  # 如果没有评论数，设置为默认值 0
        
        # 查找评论数元素
        review_element = html.xpath('//div[@class="junip-product-summary-review-count"]/text()')

        if review_element is not None:
            reviewtext = review_element[0].strip() if len(review_element) > 0 else ""
            # 提取评论数
            if "(" in reviewtext:
                reviewstr = reviewtext.replace('(', '').replace(')', '').replace(',', '').strip()
                review_count = int(reviewstr)
                ctxdata['评论数'] = review_count

        # 查找所有 product-acc-container
        acc_containers = html.xpath('//div[@class="product-acc-container"]')
        
        # 初始化面料信息
        fabric_info = None
        
        # 遍历每个 product-acc-container
        for container in acc_containers:
            # 查找标题
            heading = container.xpath('.//span[@class="product-acc-heading"]/text()')
            if heading is not None and heading[0].strip() == "Specs":
                # 查找面料信息
                specs_content = container.xpath('.//div[@class="metafield-rich_text_field"]//li/text()')
                if specs_content is None:
                    continue
                for li in specs_content:
                    if "%" in li:
                        fabric_info = li.strip()
                        break
                break  # 找到 Specs 部分后退出循环
        
        # 将面料信息保存到 ctxdata
        ctxdata['面料信息'] = fabric_info if fabric_info else "未找到面料信息"
        return ctxdata

    def parse_list(self, htmlstr) -> list:
        # 使用 lxml 解析 HTML
        html = etree.HTML(htmlstr)
        categories = html.xpath('//div[@class="variants-category"]')
        product_data = []
        i = 1
        for cate in categories:
            categoryname = ""
            categorynodes = cate.xpath('.//h2[@class="variants-category__title h4"]/span[@class="title"]/text()')
            if categories is not None:
                categoryname = categorynodes[0].strip()       
            # 查找商品信息
            products = html.xpath('//div[@class="product-card product-card--variant united-states"]')
            if products is None:
                continue
            print("--------products len--({})------".format(len(products)))
            for product in products:
                data = self.update_list_data(product)
                if data['商品地址'] == "":
                    continue
                data["品类"] = categoryname
                print("----product---category({})-i({})-({})-----".format(categoryname, i, data))
                product_data.append(data)
                i += 1
        return product_data

    def update_list_data(self, product) ->dict:
        # 获取商品链接
        product_nd = product.xpath('.//a[@class="full-unstyled-link"]/@href')
        product_link = f"{self.base_url}{product_nd[0]}" if product_nd is not None else ""

        # 获取商品标签
        tags = product.xpath('.//span[@class="product-card__badge desktop-badge"]/text()')
        tags = [tag.strip() for tag in tags if tag.strip()]

        # 获取商品图片地址
        image_url = ""
        image_nd = product.xpath('.//img[@class="product-card__featured-image"]/@src')
        image_url = "https:" + image_nd[0] if image_nd is not None else ""
        thumbnail_url = image_url.replace("width=1500", "width=300") if image_url != "" else ""

        # 获取商品标题
        titlend = product.xpath('.//p[@class="product-card__title"]/text()') # [0].strip()
        title = titlend[0].strip() if titlend is not None else ""

        # 获取商品颜色
        colornd = product.xpath('.//p[@class="product-card__color"]/text()') # [0].strip()
        color = colornd[0].strip() if colornd is not None else ""

        # 获取商品尺寸列表
        size_list = product.xpath('.//ul[@class="product-card__sizes list-unstyled grid"]/li/text()')
        size_list = [size.strip() for size in size_list if size.strip()]

        # 获取商品价格
        old_price_text = ""
        final_price_text = ""
        old_price = 0
        final_price = 0
        old_price_nd = product.xpath('.//span[@class="price-item price-item--regular"]/text()')
        if old_price_nd is not None:
            old_price_text = old_price_nd[0].strip()
            old_price = self.get_prict_by_text(old_price_text)
        final_price_nd = product.xpath('.//span[@class="price-item price-item--sale price-item--last"]/text()')
        if final_price_nd is not None:
            final_price_text = final_price_nd[0].strip()
            final_price = self.get_prict_by_text(final_price_text)
        return {
            "缩略图": thumbnail_url,
            "商品标题": title,
            "颜色": color,
            "价格": final_price_text,
            "原价": old_price,
            "销售价": final_price,
            "尺码数": len(size_list),
            "尺寸列表": ", ".join(size_list),  # 将列表转换为逗号分隔的字符串
            "标签": ", ".join(tags),  # 将列表转换为逗号分隔的字符串
            "图片地址": image_url,
            "商品地址": product_link
        }
   
    def get_prict_by_text(self, txt: str) -> float:
        if '$' in txt:
            return float(txt.replace('$', ''))
        return 0

    def request_url(self, requrl) -> str:
        if requrl in self.request_url_list:
            print("-------Skip---Request:", requrl)
            return ""
        # 发送 HTTP 请求获取网页内容
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
        response = requests.get(requrl, proxies=self.proxies, headers=headers)
        self.request_url_list.append(requrl)
        return response.text
