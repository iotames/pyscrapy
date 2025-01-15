from DrissionPage import Chromium
from service import Exporter
import json

class Aritzia:
    name = "aritzia"
    base_url = "https://www.aritzia.com"

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "Brand", "Title", "SubTitle",
        "PriceText", "FinalPrice", "OldPrice", "TotalReviews", "SizeNum", "SizeList", "Material",
        "Description", "Image", "Url"]
    }

    data_list = []

    def __init__(self):
        self.tab = Chromium().latest_tab
        self.exporter = Exporter(filename=self.name)
        self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])

    def get_row_data(self, dd) ->list:
        title_list = self.custom_settings.get("FEED_EXPORT_FIELDS", [])
        value_list = []
        for title in title_list:
            value = dd.get(title, None)
            if value is not None:
                if isinstance(value, list):
                    value = ",".join(value)
                value_list.append(value)
            else:
                value_list.append("")
        return value_list

    def run(self):
        self.tab.get('https://www.aritzia.com/us/en/clothing/sweatsuit-sets/sweat-shirts')
        for j in range(0, 30):
            print(f"----scroll_down--{j}---")
            self.tab.wait(0.8)
            self.tab.scroll.down(300)
        eles = self.tab.eles('xpath://div[@class="ar-product-grid js-product-grid center mw-100"]/ul/li')
        i = 0
        for ele in eles:
            i += 1
            print(f"---ele--({i})---({ele})--")
            # id='plp-promo-single-4'
            eleid = ele.attrs.get('id', "")
            if eleid.startswith("plp-promo-single"):
                print("-----Skip--plp-promo-single---")
                continue
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
                    self.data_list.append(dd)
                    print("---sn({})--dd({})--".format(i, dd))
            except Exception as e:
                print("-----Skip---error-----", e)
                continue
        prodcount = 0
        for dd in self.data_list:
            prodcount += 1
            print("---Begin--request_detail--count({})---requrl({})-".format(prodcount, dd.get("Url")))
            try:
                self.request_detail(dd)
            except Exception as e:
                print("-----Skip--request_detail-error-----", e)
        self.exporter.save()

    def request_detail(self, dd: dict):
        requrl = dd.get("Url")
        if requrl is None or requrl == "":
            return
        self.tab.get(requrl)
        price_ele = self.tab.ele('xpath://div[@class="product-price"]')
        if price_ele is not None:
            price_text = price_ele.text
            print("---price_text---", price_text)
            dd["PriceText"] = price_text
            try:
                def_price_ele = price_ele.ele('xpath:.//span[@class="price-default"]/span')
                def_price = def_price_ele.text
                print("---def_price---", def_price)
                if ["PriceText"] == "":
                    dd["PriceText"] = def_price
                dd["FinalPrice"] = float(def_price.replace("$", ""))
                dd["OldPrice"] = dd['FinalPrice']
            except Exception as e:
                print("------request_detail--get--def_price_ele-error-----", e)
                standard_price_ele = price_ele.ele('xpath:.//span[@class="price-standard strike dib"]/span')
                if standard_price_ele is not None:
                    standard_price = standard_price_ele.text
                    print("---standard_price---", standard_price)
                    dd["OldPrice"] = float(standard_price.replace("$", ""))
                final_price_ele = price_ele.ele('xpath:.//span[@class="price-sales red"]/span')
                if final_price_ele is not None:
                    final_price = final_price_ele.text
                    print("---final_price---", final_price)
                    if final_price != "" and dd['PriceText'] == "":
                        dd["PriceText"] = final_price
                    dd["FinalPrice"] = float(final_price.replace("$", ""))
        size_eles = self.tab.eles('xpath://ul[@class="overflow-auto pv3 js-sheet__scroll"]/li')
        size_list = []
        for size_ele in size_eles:
            size_ele_text = size_ele.text
            print("---size_ele_text---", size_ele_text)
            size_list.append(size_ele_text)
        dd['SizeNum'] = len(size_list)
        dd['SizeList'] = size_list
        desc_eles = self.tab.eles('xpath://span[@class="pdp-tab-title db mt3 mb2"][contains(text(),"Materials")]/parent::div/div[@class="js-product-accordion__content"]/ul/li')
        desc_list = []
        for desc_ele in desc_eles:
            desc_ele_text = desc_ele.text
            desc_list.append(desc_ele_text)
            print("---desc_ele_text---", desc_ele_text)
            if '%' in desc_ele_text:
                dd['Material'] = desc_ele_text
        dd['Description'] = "|".join(desc_list)
        # //span[@class="dn db-ns"]
        dd['SubTitle'] = self.get_text_by_xpath(self.tab, '//span[@class="dn db-ns"]')
        dd['Image'] = self.get_attr_by_xpath(self.tab, "src", '//img[@class="db w-100 lazy ar-product-detail__product-image js-product-detail__product-image"]')
        thumbnail = dd.get("Thumbnail", "")
        if thumbnail != "" and thumbnail.startswith("//") and dd['Image'] != "":
            thumbnail = dd['Image'].replace("/large/", "/medium/").replace("/w_1200/", "/medium/")
            if thumbnail.endswith("_on_a"):
                thumbnail = thumbnail + ".jpg"
        dd['Thumbnail'] = thumbnail
        try:
            # //div[@class="pdp-tt-reviews__summary-count"]
            review_ele = self.tab.ele('xpath://div[@class="pdp-tt-reviews__summary-count"]')
            if review_ele is not None:
                review_text = review_ele.text
                print("---review_text---", review_text)
                dd['TotalReviews'] = int(review_text.replace(",", "").strip())
        except Exception as e:
            print("-----Skip--request_detail--get--review_text-error-----", e)
        print("-------parse--detail--({})---".format(dd))
        rowdt = self.get_row_data(dd)
        self.exporter.append_row(rowdt)

    def get_text_by_xpath(self, ele, xpath: str) -> str:
        try:
            elee = ele.ele('xpath:{}'.format(xpath))
            if elee is not None:
                print("---get_text_by_xpath({})-text({})---".format(xpath, elee.text))
                return elee.text.strip()
        except Exception as e:
            print("-----Skip--get_text_by_xpath({})-error({})-----", xpath, e)
            return ""
    def get_attr_by_xpath(self, ele, attrname: str, xpath: str) -> str:
        try:
            elee = ele.ele('xpath:{}'.format(xpath))
            if elee is not None:
                attrval = elee.attrs.get(attrname, "")
                print("---get_text_by_xpath({})--attr({})({})---".format(xpath, attrname, attrval))
                return attrval
        except Exception as e:
            print("-----Skip--get_attr_by_xpath({})-error({})-----", xpath, e)
            return ""

    # def export(self):
    #     pass