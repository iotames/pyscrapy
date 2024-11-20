# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
import hashlib
from scrapy.utils.python import to_bytes
import os
from service import Config
# from pyscrapy.process.product import ProcessProductBase

cf = Config.get_instance()


class ImagePipeline(ImagesPipeline):
    
    # def process_item(self, item, spider):
    #     if 'image_urls' not in item:
    #         print("-----ProductDetail.process_item--image_urls not in item--")
    #         item['image_urls'] = [item['Thumbnail']]
    #     # 必须返回item。image_urls 添加处理要写在上一个管道才可
    #     return item

    @staticmethod
    def get_guid_by_url(url: str) -> str:
        print(url)
        return hashlib.md5(to_bytes(url)).hexdigest()

    def file_path(self, request, response=None, info: ImagesPipeline.SpiderInfo = None, *, item=None): 
        filepath = self.get_local_file_path_by_url(request.url, info.spider.get_images_dirname())
        print("-----ImagePipeline.file_path--request.url({})--filepath({})--".format(request.url, filepath))
        return filepath

    @classmethod
    def get_local_file_path_by_url(cls, url, dirname: str):
        dirpath = os.path.join(cf.get_images_path(), dirname)
        filepath = os.path.join(dirpath, cls.get_guid_by_url(url) + ".jpg")
        print("------get_local_file_path_by_url---dirpath=", dirpath, filepath)
        return filepath
        # return "runtime/downloads/images/{}.jpg".format(cls.get_guid_by_url(url))

    def get_media_requests(self, item, info: ImagesPipeline.SpiderInfo):
        urls = ItemAdapter(item).get(self.images_urls_field, [])  # item['image_urls']
        print(f"--------ImagePipeline.get_media_requests--image_referer({info.spider.image_referer})--urls({urls})")
        spider = info.spider
        # return [Request(u) for u in urls]
        for image_url in urls:
            # meta = None
            file_path = self.get_local_file_path_by_url(image_url, spider.get_images_dirname())
            if os.path.isfile(file_path):
                print(f'----Skip Download ImageUrl. File Exists. {image_url} => {file_path}')
                continue
            print(f"-----Begin Download Image({image_url})-to-({file_path})---")
            if spider.image_referer:
                # meta = {"referer": spider.image_referer} referer无效
                yield Request(image_url, headers={'Referer': spider.image_referer})
            else:
                yield Request(image_url)

    def item_completed(self, results, item, info: ImagesPipeline.SpiderInfo):
        print('==========ImagePipeline======item_completed==========')
        print(results)
        # results [] or [(True, {'url': '', 'path': 'dir/file.jpg', 'checksum': '', 'status': 'uptodate'})]
        # [(False, <twisted.python.failure.Failure scrapy.pipelines.files.FileException: >)]
        
        # 初始化一个列表来存储成功的图片路径
        image_paths = []

        # 遍历 results，处理成功和失败的下载
        for ok, x in results:
            if ok:
                image_paths.append(x['path'])
            else:
                print(f"-----ImagePipeline--item_completed--Exception({str(x)})--")
                raise x

        adapter = ItemAdapter(item)
        urls_field = self.images_urls_field

        if urls_field in item:
            if not image_paths:
                image_paths = []
                for url in item[urls_field]:
                    file_path = self.get_local_file_path_by_url(url, info.spider.get_images_dirname())
                    if os.path.isfile(file_path):
                        image_paths.append(file_path)

            adapter['image_paths'] = image_paths
        print(f"-------urls_field({urls_field})--image_paths({image_paths})--")

        # 如果没有成功下载的图片，可以抛出一个异常或记录日志
        if not image_paths:
            # 如果你希望在这种情况下抛出异常，可以取消注释下面的代码
            raise Exception("image_paths is empty")
        return item
