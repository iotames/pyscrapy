from DrissionPage import Chromium #, NoneElement
# from DrissionPage.errors import ElementNotFoundError
from service import Exporter, Logger, Config
import os


class Ms365:
    name = "ms365"
    base_url = "https://cottononcomau.sharepoint.com"
    start_url = "https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE"
    lg: Logger
    download_path: str
    # download_files = []

    # https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/SUPPLIER%20X/Forms/AllItems.aspx

    custom_settings = {
        'FEED_EXPORT_FIELDS': ["序号", "供应商", "文件路径", "文件大小",  "链接地址"]
    }

    def __init__(self):
        self.exporter = Exporter(filename=self.name)
        self.exporter.append_row(self.custom_settings['FEED_EXPORT_FIELDS'])
        self.tab = Chromium().latest_tab
        self.lg = Logger.get_instance()
        self.lg.echo_msg = True
        downpath = Config.get_instance().get_root_path()
        self.download_path = os.path.join(downpath, 'runtime', 'downloads', 'pdf')

    def run(self):
        print("Start Run", self.name)
        vendor_list = self.get_vendor_list()
        vii = 0
        for v in vendor_list:
            vii += 1
            vendor_urlkey = v.get('urlkey')
            vendor_url = v.get('url')
            vendor_name =  v.get('name')
            subdirname = "Inspection Reports"
            filedirpath = os.path.join(self.download_path, vendor_name)
            fullfilepath = os.path.join(filedirpath, subdirname+".zip")
            zipsize = 0
            if os.path.exists(fullfilepath):
                zipsize = os.path.getsize(fullfilepath)
                self.lg.debug("---index({})--file_exists---vendor_name=({})---fullfilepath({})--zipsize({})--".format(vii, vendor_name, fullfilepath, zipsize))
                self.exporter.append_row([vii, vendor_name, fullfilepath, zipsize, vendor_url])
                continue
            fulldirpath = os.path.join(filedirpath, subdirname)
            if os.path.isdir(fulldirpath):
                self.lg.debug("---index({})--dir_exists---vendor_name=({})---fulldirpath({})---".format(vii, vendor_name, fulldirpath))
                raise Exception("dir_exists:"+fulldirpath)
   
            self.lg.debug("---index({})--vendor_name=({})--vendor_urlkey({})--to--url({})".format(vii, vendor_name, vendor_urlkey, vendor_url))
            self.tab.get(vendor_url)
            self.tab.wait(2)
            if self.click_to_dirname(subdirname):
                self.lg.debug("----index({})--click_to_dirname.success---vendor_name=({})---url({})".format(vii, v.get('name'), vendor_url))
                try:
                    # os.makedirs(filedirpath, exist_ok=True)
                    self.lg.debug("---index({})--download_file---vendor_name=({})---fullfilepath({})---".format(vii, vendor_name, fullfilepath))
                    self.tab.set.download_path(filedirpath)
                    self.tab.set.download_file_name(subdirname)
                    self.tab.ele('xpath://div[@role="group"]//button[@name="下载"]').click() # 该元素没有位置及大小。
                    self.tab.wait.download_begin()  # 等待下载开始
                    self.tab.wait.downloads_done()  # 等待所有任务结束
                    self.exporter.append_row([vii, vendor_name, fullfilepath, os.path.getsize(fullfilepath), vendor_url])
                except Exception as e:
                    self.lg.debug("----index({})----download_file_-err-vendor_name=({})---fullfilepath({})--({})-".format(vii, vendor_name, fullfilepath, e))

                # elebtns = self.tab.eles('xpath://button[@data-automationid="FieldRenderer-name"]')
                # for elebtn in elebtns:
                #     btntxt = elebtn.text
                #     if '.pdf' in btntxt:
                #         urlpre = 'https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/_layouts/15/download.aspx?SourceUrl=/sites/COTTONONQUALITYCOMPLIANCE'
                #         url = "{}/{}/{}/{}".format(urlpre, vendor_urlkey, subdirname, btntxt)
                #         # self.download_files.append({"vendor_name": vendor_name, 'vendor_urlkey': vendor_urlkey, 'filename': btntxt, 'url': url})
                #         filedirpath = os.path.join(self.download_path, vendor_name, subdirname)
                #         filepath = os.path.join(filedirpath, btntxt)
                #         if os.path.exists(filepath):
                #             self.lg.debug("---file_exists---vendor_name=({})---url({})---".format(vendor_name, url))
                #         else:
                #             self.lg.debug("---download_file---vendor_name=({})---url({})---".format(vendor_name, url))
                #             self.tab.download(url, filedirpath)
                #         self.exporter.append_row([vendor_name, vendor_urlkey, btntxt, url])
                # https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/_layouts/15/download.aspx?SourceUrl=/sites/COTTONONQUALITYCOMPLIANCE/SUPPLIER Z/Inspection Reports/PASS-CHAOZHOU HUICHENG SHOES - Style  4592957 - FOOTWEAR - FI1-20Aug2024.pdf
            else:
                self.lg.debug("---click_to_dirname.error---vendor_name=({})---Inspection Reports".format(vendor_name))
        self.exporter.save()

    def click_to_dirname(self, dirname: str) ->bool:
        btn = self.tab.ele('xpath://button[contains(text(),"{}")]'.format(dirname))
        try:
            btn.click()
            # return btn.text.strip()
            return True
        except Exception as e:
            # from DrissionPage.errors import ElementNotFoundError
            self.lg.debug("-----click_to_dirname.error({})".format(e))
            # return ""
            return False

    def get_vendor_list(self):
        self.tab.get(self.start_url)
        self.tab.wait(1)
        vendoreles1 = self.tab.eles('xpath://div[@role="list"]/span/a')
        vendor_list = []
        for vele1 in vendoreles1:
            vendorurl = vele1.attr("href")
            if '/Forms/AllItems.aspx' in vendorurl:
                urlkey = vendorurl.replace('/Forms/AllItems.aspx', '').replace('https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/', '')
                vendor_list.append({'name': vele1.text.strip(), 'url': vendorurl, 'urlkey': urlkey})
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
            if '/Forms/AllItems.aspx' in vendorurl:
                urlkey = vendorurl.replace('/Forms/AllItems.aspx', '').replace('https://cottononcomau.sharepoint.com/sites/COTTONONQUALITYCOMPLIANCE/', '')
                vendor_list.append({'name': vele2.text.strip(), 'url': vendorurl, 'urlkey': urlkey})
        self.lg.debug("---------vendor_list.len={}".format(len(vendor_list)))
        # for v in vendor_list:
        #     self.lg.debug("---------vendor_info=({})".format(v))
        return vendor_list