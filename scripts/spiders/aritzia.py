from DrissionPage import Chromium
from service import Exporter
import json

class Aritzia:
    name = "aritzia"
    base_url = "https://www.aritzia.com"

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "PublishedAt", "CategoryName", "Vendor", 
        "Title", "VariantTitle", "PriceRatio", "Price", "OriginalPrice", "VariantsCount", "TotalInventoryQuantity", "InventoryAvailable", "RecentlyOrderedCount",
        "Grams", "BodyHtmlSafe", "ProductImage", "Url"]
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
            dd.get("Code"),
            dd.get("published_at"),
            dd.get("product_type"),
            dd.get("vendor"),
            dd.get("title"),
            dd.get("variant_title"),
            dd.get("price_ratio"), # 折扣
            dd.get("price"),
            dd.get("OldPrice"),
            dd.get("variants_count"), # SizeNum
            dd.get("inventory_quantity"), # TotalInventoryQuantity
            dd.get("inventory_available"),
            dd.get("recently_ordered_count"),
            dd.get("grams"),
            # ",".join(dd.get("collections")),
            # ",".join(dd.get("tags")),
            dd.get("body_html_safe"),
            dd.get("product_image"),
            produrl
        ]

    def run(self):
        self.tab.get('https://www.aritzia.com/us/en/clothing/sweatsuit-sets/sweat-shirts')
        for j in range(0, 22):
            print(f"----scroll_down--{j}---")
            self.tab.wait(0.6)
            self.tab.scroll.down(300)
        eles = self.tab.eles('xpath://div[@class="ar-product-grid js-product-grid center mw-100"]/ul/li')
        i = 0
        for ele in eles:
            try:
                info_ele = ele.ele('xpath:.//div')
                if info_ele is not None:
                    jsonstr = info_ele.attrs.get('data-master', None)
                    if jsonstr is None:
                        continue
                    info = json.loads(jsonstr)
                    aele = ele.ele('xpath:.//a')
                    purl = ""
                    if aele is not None:
                        purl = aele.attrs.get('href', "")
                    thumbnail = ""
                    imgele = ele.ele('xpath:.//img')
                    if imgele is not None:
                        thumbnail = imgele.attrs.get('src', "")
                    dd = {
                        "Code": info.get("master"),
                        "OldPrice": float(info.get("price", 0)),
                        "Brand": info.get("brand"),
                        "Title": info.get("name"),
                        "Thumbnail": thumbnail,
                        "Url": purl
                    }
                    # pricetextele = ele.ele('xpath:.//span[@class="js-product__sales-price"]')
                    # if pricetextele is not None:
                    #     dd["PriceText"] = pricetextele.text
                    # rowdt = self.get_row_data(dd)
                    # self.exporter.append_row(rowdt)
                    i += 1
                    print("---sn({})--dd({})--".format(i, dd))
            except Exception as e:
                print("--------error-----", e)
                continue

        # self.exporter.save()