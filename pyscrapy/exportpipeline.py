from scrapy.exporters import BaseItemExporter
import os, openpyxl # csv
from scrapy import signals
from service import Logger
# from pyscrapy.items import  BaseProductItem

class XlsxExporter(BaseItemExporter):

    __fields_to_export: list

    def __init__(self, file, **kwargs):
        lg = Logger()
        lg.debug(f"-----XlsxExporter---__init__---kwargs({kwargs})---")
        self.__fields_to_export = kwargs['fields_to_export']
        self.file = file
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "Scraped Data"
        self.header_written = False
        super().__init__(dont_fail=True, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        lg = Logger()
        lg.debug(f"-------from_crawler---{args}--{kwargs}----")
        
        # 从命令行参数中获取输出文件名
        # output_file = crawler.settings.get('FEEDS', {}).get('output', {}).get('uri', 'output.xlsx')
        output_file = crawler.settings.get('FEED_URI', 'output.xlsx')
        pipeline = cls(file=output_file, **kwargs)
        crawler.signals.connect(pipeline.open_spider, signals.spider_opened)
        crawler.signals.connect(pipeline.close_spider, signals.spider_closed)
        return pipeline

    def open_spider(self, spider):
        # 初始化操作，例如打开文件或创建工作簿
        pass

    def close_spider(self, spider):
        if os.path.exists(self.file):
            print(f"Warning: File {self.file} already exists and will be overwritten.")
        self.wb.save(self.file)

    def process_item(self, item, spider):
        lg = Logger()
        lg.debug(f"----------XlsxExporter---process_item----------item{item}--")
    def export_item(self, item):
        lg = Logger()
        lg.debug(f"-----XlsxExporter---export_item---__fields_to_export({self.__fields_to_export})--")
        # lg.debug(f"----------XlsxExporter---export_item------item({item})--")
        if not item:
            return item
        row = []
        for k in self.__fields_to_export:
            v = item[k]
            if v:
                if k == 'SizeList':
                    v = ",".join(v)
                row.append(v)
            else:
                row.append("")
        if not self.header_written:
            # self.ws.append(list(item.keys()))
            self.ws.append(list(self.__fields_to_export))
            self.header_written = True
        lg.debug(f"-----XlsxExporter---process_item---row({row})---")
        self.ws.append(list(row))
        return item