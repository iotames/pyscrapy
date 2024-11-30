from DrissionPage import Chromium
from service import Exporter


class Vqfit:
    name = "vqfit"
    base_url = "https://www.vqfit.com"

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "PublishedAt", "CategoryName", "Vendor", 
        "Title", "VariantTitle", "PriceRatio", "Price", "OriginalPrice", "VariantsCount", "TotalInventoryQuantity", "InventoryAvailable", "RecentlyOrderedCount",
        "Grams", "Collections", "Tags", "BodyHtmlSafe", "ProductImage", "Url"]
    }

    def __init__(self):
        self.tab = Chromium().latest_tab
        self.exporter = Exporter(filename=self.name)
        self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])

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
        self.tab.listen.start("https://7u6fcx4gmf-dsn.algolia.net/1/indexes/*/queries")
        self.tab.get('https://www.vqfit.com/collections/all')
        i = 0
        for packet in self.tab.listen.steps():
            i += 1
            for j in range(0, 8):
                print(f"----scroll_down--{j}---")
                self.tab.wait(0.2)
                self.tab.scroll.down(300)
            result = packet.response.body
            for dd in result.get("results")[0].get("hits"):
                rowdt = self.get_row_data(dd)
                # print("-----rowdata----", rowdt)
                self.exporter.append_row(rowdt)
            # postdata = packet.request.postData
            # raw_data = packet.request.raw_post_data
            print(f"-----vqfit--run--[{i}]--requrl({packet.url})-----")
            if i == 24:
                break
            try:
                self.tab.ele('xpath://a[@aria-label="Next Page"]').click()
            except:
                pass
        self.exporter.save()
