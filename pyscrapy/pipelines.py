# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Item, Request
from scrapy.pipelines.images import ImagesPipeline
import hashlib
from scrapy.utils.python import to_bytes
import os
from service import Config
from .items import FromPage, BaseProductItem
from .dbpipeline import ProductDetail
# from pyscrapy.process.product import ProcessProductBase

cf = Config.get_instance()



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
        # [(False, <twisted.python.failure.Failure scrapy.pipelines.files.FileException: >)]
        
        # 初始化一个列表来存储成功的图片路径
        image_paths = []
        # 初始化一个列表来存储失败的图片 URL
        failed_urls = []

        # 遍历 results，处理成功和失败的下载
        for ok, x in results:
            if ok:
                image_paths.append(x['path'])
            else:
                # 如果下载失败，记录失败的 URL
                # failed_urls.append(x.get('url', 'Unknown URL'))
                # self.logger.error(f"Failed to download image: {x.get('url', 'Unknown URL')}")
                raise Exception("Item contains no successfully downloaded images:")

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
            # 将失败的 URL 存储在 item 中
            adapter['failed_urls'] = failed_urls

        # 如果没有成功下载的图片，可以抛出一个异常或记录日志
        if not image_paths:
            self.logger.warning("Item contains no successfully downloaded images")
            # 如果你希望在这种情况下抛出异常，可以取消注释下面的代码
            # raise DropItem("Item contains no successfully downloaded images")

        return item
