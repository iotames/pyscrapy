from DrissionPage import Chromium
from service import Exporter, Logger


class Ms365:
    name = "ms365"
    base_url = "https://cottononcomau.sharepoint.com"
    start_url = "https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE"
    lg: Logger

    # https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/SUPPLIER%20X/Forms/AllItems.aspx

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["Thumbnail", "Code", "CategoryName",  "Url"]
    }

    def __init__(self):
        self.tab = Chromium().latest_tab
        self.exporter = Exporter(filename=self.name)
        self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])
        self.lg = Logger.get_instance()
        self.lg.echo_msg = True

    def run(self):
        print("Start Run", self.name)
        vendor_list = self.get_vendor_list()
        vii = 0
        for v in vendor_list:
            vii += 1
            self.lg.debug("---index({})--vendor_name=({})---url({})".format(vii, v.get('name'), v.get('url')))
        self.exporter.save()

    def get_vendor_list(self):
        self.tab.get(self.start_url)
        self.tab.wait(1)
        vendoreles1 = self.tab.eles('xpath://div[@role="list"]/span/a')
        vendor_list = []
        for vele1 in vendoreles1:
            vendorurl = vele1.attr("href")
            # print(vele1.text, vendorurl)
            if '/Forms/AllItems.aspx' in vendorurl:
                vendor_list.append({'name': vele1.text.strip(), 'url': vendorurl})
        self.lg.debug("---------vendor_list.len={}".format(len(vendor_list)))
        more_btn_xpath = 'xpath://div[@class="ms-HorizontalNavItems"]/div[2]'
        self.tab.wait(1)
        self.tab.ele(more_btn_xpath).wait.displayed()
        self.tab.ele(more_btn_xpath).click()
        self.tab.wait(2)
        vendoreles2 = self.tab.eles('xpath://ul[@role="presentation"]/li/div/a')
        # //ul[@role="presentation"]/li/div/a/div/span
        for vele2 in vendoreles2:
            vendorurl = vele2.attr("href")
            # print(vele2.text, vendorurl)
            if '/Forms/AllItems.aspx' in vendorurl:
                vendor_list.append({'name': vele2.text.strip(), 'url': vendorurl})
        self.lg.debug("---------vendor_list.len={}".format(len(vendor_list)))
        return vendor_list