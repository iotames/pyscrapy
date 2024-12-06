from DrissionPage import Chromium
from service import Exporter, Logger


class Vuoriclothing:
    name = "vuoriclothing"
    base_url = "https://vuoriclothing.com"
    lg: Logger

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "PublishedAt", "CategoryName", "Vendor", 
        "Title", "VariantTitle", "PriceRatio", "Price", "OriginalPrice", "VariantsCount", "TotalInventoryQuantity", "InventoryAvailable", "RecentlyOrderedCount",
        "Grams", "Collections", "Tags", "BodyHtmlSafe", "ProductImage", "Url"]
    }

    def __init__(self):
        self.lg = Logger.get_instance()
        self.lg.echo_msg = True
        self.tab = Chromium().latest_tab
        # self.exporter = Exporter(filename=self.name)
        # self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])

    def get_row_data(self, dd) ->list:
        urlKey = dd.get("handle")
        produrl = f"{self.base_url}/products/{urlKey}"
        thumbnail = dd.get("product_image")+"&width=200"
        return [
            thumbnail,
            dd.get("sku"),
            dd.get("published_at"),
            dd.get("product_type"),
            dd.get("vendor"),
            dd.get("title"),
            dd.get("variant_title"),
            dd.get("price_ratio"), # 折扣
            dd.get("price"),
            dd.get("compare_at_price"),
            dd.get("variants_count"), # SizeNum
            dd.get("inventory_quantity"), # TotalInventoryQuantity
            dd.get("inventory_available"),
            dd.get("recently_ordered_count"),
            dd.get("grams"),
            ",".join(dd.get("collections")),
            ",".join(dd.get("tags")),
            dd.get("body_html_safe"),
            dd.get("product_image"),
            produrl
        ]

    def run(self):        
        self.tab.listen.start("https://p2mlbkgfds-dsn.algolia.net/1/indexes/*/queries")
        url_list = [
            "https://vuoriclothing.com/collections/womens",
            "https://vuoriclothing.com/collections/mens"
        ]
        for requrl in url_list:
            self.tab.get(requrl)
            # currenturl = self.tab.url
            print("请确认是否继续下一步操作 (输入 'y' 或 'yes' 继续:")
            # 等待用户输入
            confirmation = input().strip().lower()
            # 检查用户输入
            if confirmation in ['y', 'yes']:
                print("继续执行下一步操作...")
                continue
            else:
                raise Exception("用户取消操作")
        self.listen_xhr_data()
        # self.exporter.save()

    def listen_xhr_data(self):
        i = 0
        for packet in self.tab.listen.steps():
            if packet.request.method.upper() == 'GET':
                continue
            i += 1
            postdata = packet.request.postData
            result = packet.response.body
            self.lg.debug(f"-----{i}--{packet.request.method}--postdata({postdata})----result({result})--")
 
            # for dd in result.get("results")[0].get("hits"):
            #     # rowdt = self.get_row_data(dd)
            #     # print("-----rowdata----", rowdt)
            #     self.lg.debug(f"-----rowdata({dd})----")
                # self.exporter.append_row(rowdt)
            # postdata = packet.request.postData
            # raw_data = packet.request.raw_post_data
