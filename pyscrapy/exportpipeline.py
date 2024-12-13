from scrapy.exporters import BaseItemExporter
import os, openpyxl
from scrapy import signals
from service import Logger
import exporter as exporterdata
# from pyscrapy.items import  BaseProductItem

class XlsxExporter(BaseItemExporter):

    __fields_to_export: list

    def __init__(self, file, **kwargs):
        lg = Logger()
        lg.debug(f"-----XlsxExporter---__init__file({file})---kwargs({kwargs})---")
        self.__fields_to_export = kwargs['fields_to_export']
        self.file = file
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "ScrapedData"
        self.header_written = False
        super().__init__(dont_fail=True, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 会捕获到*args参数： <_io.BufferedWriter name='yourfilename.xlsx'>
        lg = Logger()
        lg.debug(f"-------from_crawler---[{args}]--{args[0].name}--{kwargs}--")

        # 从命令行参数中获取输出文件名
        # 捕获 -o 参数的文件名。也可以通过 custom_settings 的 FEED_URI 参数获取 output_file。
        # output_file = crawler.settings.get('FEED_URI', 'output.xlsx')
        output_file = args[0].name
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

    # process_item：scrapy.exporters.BaseItemExporter 是特殊的管道，用来导出爬虫数据。
    # 通过爬虫的 -o 参数，或者 FEED_URI 等相关配置，触发调用 export_item 方法，不会调用process_item。
    def process_item(self, item, spider):
        lg = Logger()
        lg.debug(f"----------XlsxExporter---process_item----------item{item}--")
    def export_item(self, item):
        # lg = Logger()
        # lg.debug(f"-----XlsxExporter---export_item---__fields_to_export({self.__fields_to_export})--")
        # lg.debug(f"----------XlsxExporter---export_item------item({item})--")
        if not item:
            return item
        if not self.header_written:
            # self.ws.append(list(item.keys()))
            self.ws.append(list(self.__fields_to_export))
            self.header_written = True
        row = exporterdata.get_row_data(self.__fields_to_export, item)
        self.ws.append(list(row))
        # lg.debug(f"-----XlsxExporter---process_item---row({row})---")
        return item
