# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Item, Request, signals
from scrapy.pipelines.images import ImagesPipeline
import hashlib
from scrapy.utils.python import to_bytes
import os, csv, openpyxl
from scrapy.exporters import BaseItemExporter
from service import Config
from .items import BaseProductItem
from pyscrapy.process.product import ProcessProductBase

cf = Config.get_instance()

process_map = {
    BaseProductItem: ProcessProductBase(),
}

class PyscrapyPipeline:
    def process_item(self, item: Item, spider):
        print('====================== PyscrapyPipeline : process_item ===================')
        if type(item) in process_map:
            process_map[type(item)].process_item(item, spider)
        else:
            msg = "Item对象 {} 在管道处理中没有找到process处理类。 请在 process_map 字典中添加对应关系。".format(item.__class__.__name__)
            raise RuntimeError(msg)


class ExportPipeline(BaseItemExporter):

    def __init__(self, file, **kwargs):
        self._configure(kwargs)
        self.file = file
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = "Scraped Data"
        self.header_written = False

    @classmethod
    def from_crawler(cls, crawler):
        # 从命令行参数中获取输出文件名
        output_file = crawler.settings.get('FEEDS', {}).get('output', {}).get('uri', 'output.xlsx')
        pipeline = cls(file=output_file)
        crawler.signals.connect(pipeline.open_spider, signals.spider_opened)
        crawler.signals.connect(pipeline.close_spider, signals.spider_closed)
        return pipeline

    def open_spider(self, spider):
        # 初始化操作，例如打开文件或创建工作簿
        pass

    def close_spider(self, spider):
        self.wb.save(self.file)

    def process_item(self, item, spider):
        if not self.header_written:
            self.ws.append(list(item.keys()))
            self.header_written = True

        self.ws.append(list(item.values()))
        return item


class ImagePipeline(ImagesPipeline):

    # def process_item(self, item, spider):
    #     if isinstance(item, GympluscoffeeGoodsImageItem):
    #         return super(ImagePipeline, self).process_item(item, spider)

    @staticmethod
    def get_guid_by_url(url: str) -> str:
        print(url)
        return hashlib.md5(to_bytes(url)).hexdigest()

    def file_path(self, request, response=None, info: ImagesPipeline.SpiderInfo = None, *, item=None):
        image_guid = self.get_guid_by_url(request.url)
        image_path = f'{info.spider.get_images_dirname()}/{image_guid}.jpg'
        return image_path

    @classmethod
    def get_local_file_path_by_url(cls, url, spider):
        dir_path = os.path.join(cf.get_images_path(), spider.get_images_dirname())
        print("-------pipelines---image---dir_path=", dir_path)
        return dir_path + os.path.sep + cls.get_guid_by_url(url) + ".jpg"

    def get_media_requests(self, item, info: ImagesPipeline.SpiderInfo):
        print('=========ImagePipeline=======get_media_requests====(Download image)======')
        urls = ItemAdapter(item).get(self.images_urls_field, [])  # item['image_urls']
        print(urls)
        spider = info.spider
        # return [Request(u) for u in urls]
        for image_url in urls:
            meta = None
            file_path = self.get_local_file_path_by_url(image_url, spider)
            if os.path.isfile(file_path):
                print(f'Skip Download ImageUrl. File Exists. {image_url} => {file_path}')
                continue
            if spider.image_referer:
                meta = {"referer": spider.image_referer}
            print(f"Begin Download Image: {image_url} => {file_path}")
            yield Request(image_url, meta=meta)

    def item_completed(self, results, item, info: ImagesPipeline.SpiderInfo):
        print('==========ImagePipeline======item_completed==========')
        print(results)
        # results [] or [(True, {'url': '', 'path': 'dir/file.jpg', 'checksum': '', 'status': 'uptodate'})]
        image_paths = [x['path'] for ok, x in results if ok]
        adapter = ItemAdapter(item)
        urls_field = self.images_urls_field
        if urls_field in item:
            if not image_paths:
                image_paths = []
                for url in item[urls_field]:
                    file_path = self.get_local_file_path_by_url(url, info.spider)
                    if os.path.isfile(file_path):
                        image_paths.append(info.spider.get_images_dirname() + os.path.sep + self.get_guid_by_url(url) + '.jpg')
            adapter['image_paths'] = image_paths
        # if not image_paths:
        #     raise DropItem("Item contains no images")
        # print(item)
        return item
