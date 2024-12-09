from DrissionPage import Chromium
from service import Exporter, Logger


class Vuoriclothing:
    name = "vuoriclothing"
    base_url = "https://vuoriclothing.com"
    lg: Logger

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "CategoryName",
        "Title", "Color", "Price", "TotalInventoryQuantity",
        "SizeNum", "SizeList", "ProductImage", "Url"]
    }

    def __init__(self):
        self.lg = Logger.get_instance()
        self.lg.echo_msg = True
        self.tab = Chromium().latest_tab
        self.exporter = Exporter(filename=self.name)
        self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])

    def get_row_data(self, dd) ->list:
        urlKey = dd.get("handle")
        produrl = f"{self.base_url}/products/{urlKey}"
        image = dd.get("image")
        thumbnail = image+"&width=200"
        size_num = len(dd.get("variants"))
        size_list = []
        for vv in dd.get("variants"):
            size_list.append(vv.get("options").get("Size"))
        total_inventory_quantity = 0
        color = ''
        if 'online_inventory_available_by_option' in dd:
            if 'Color' in dd['online_inventory_available_by_option']:
                for k, v in dd['online_inventory_available_by_option']['Color'].items():
                    color = k
                    total_inventory_quantity += v.get("quantity", 0)    
        return [
            thumbnail,
            dd.get("objectID"),
            dd.get("product_type"),
            dd.get("title"),
            color,
            dd.get("variants_min_price"),
            total_inventory_quantity,
            size_num,
            ",".join(size_list),
            image,
            produrl
        ]

    def run(self):        
        self.tab.listen.start("https://p2mlbkgfds-dsn.algolia.net/1/indexes/*/queries")
        # self.tab.listen.start("https://p2mlbkgfds-1.algolianet.com/1/indexes/*/queries")

        url_list = [
            "https://vuoriclothing.com/collections/womens",
            "https://vuoriclothing.com/collections/mens"
        ]
        self.tab.get(url_list[1])            
        self.listen_xhr_data()
        self.exporter.save()

    def listen_xhr_data(self):
        currenturl = self.tab.url
        groupname = currenturl.split("/")[-1]
        i = 0
        j = 0
        for packet in self.tab.listen.steps():
            self.lg.debug(f"---Listen({groupname})--to({currenturl})--xhrurl({packet.request.url})")
            if packet.request.method.upper() == 'GET':
                self.lg.debug("-----Skip--GET--packet--url({})".format(packet.request.url))
                continue
            postdata = packet.request.postData
            result = packet.response.body
            if not result:
                self.lg.debug("-----Skip--result--None--packet--url({})".format(packet.request.url))
                continue
            # self.tab.listen.wait()
            i += 1
            if 'results' in result:
                if 'requests' not in postdata:
                    continue
                if len(postdata['requests']) != len(result['results']):
                    self.lg.debug("------request--param--url({})".format(packet.request.url))
                    continue
                if len(result['results']) == 2:
                    # self.lg.debug("------request--params-url({})--params({})".format(packet.request.url, postdata['requests'][1]['params']))
                    if r'AND%20NOT%20named_tags.gated%3Ainternal-influencer-accepted' in postdata['requests'][1]['params'] and 'page' in result['results'][1]:
                        # if result['results'][1]['page'] == j:
                        page_index = result['results'][1]['page']
                        total_page = result['results'][1]['nbPages']
                        dds = result.get("results")[1].get("hits")
                        for dd in dds:
                            rowdata = self.get_row_data(dd)
                            # self.lg.debug(f"-----rowdata({dd})---rowdata({rowdata})---")
                            self.exporter.append_row(rowdata)
                        self.lg.debug(f"-----listen_xhr_data----i({i})-j({j})--page_index({page_index})--total_page({total_page})--dds.len({len(dds)})--groupname({groupname})---Method({packet.request.method})---")
                        j +=1
                        if page_index < (total_page - 3):
                            continue
                        if page_index >= (total_page-1):
                            break
                        # if groupname == "mens" and page_index > 3: # page_index >= total_page:
                        print("请确认是否继续下一步操作 (输入 'y'  继续，输入 'n' 退出):")
                        # 等待用户输入
                        confirmation = input().strip().lower()
                        # 检查用户输入
                        if confirmation in ['y', 'yes']:
                            pass
                        if confirmation in ['n', 'no']:
                            print("退出操作。")
                            break
            print("继续执行下一步操作...")
