from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pyscrapy.enum.spider import *
from Config import Config
from service import DB
from pyscrapy.models import Table
# https://github.com/pyinstaller/pyinstaller/issues/4815
import scrapy.utils.misc
import scrapy.core.scraper


def warn_on_generator_with_return_value_stub(spider, callable):
    pass


scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub


class Spider:

    @staticmethod
    def crawl(name: str, spider_args=None, output=None):
        process = CrawlerProcess(get_project_settings())
        process.crawl(name, **spider_args)
        process.start()

        # cmd_list = ['scrapy', 'crawl', name]
        # if output:
        #     # 输出爬虫结果到文件
        #     cmd_list.extend(['-o', output])
        # if spider_args:
        #     for key, value in spider_args.items():
        #         cmd_list.extend(['-a', key + "=" + value])
        # cmdline.execute(cmd_list)

    @staticmethod
    def create_all_tables():
        config = Config()
        db = DB(config.get_database())
        db.ROOT_PATH = config.ROOT_PATH
        engine = db.get_db_engine()
        Table.create_all_tables(engine)


if __name__ == '__main__':
    # Spider.create_all_tables()
    dirpath = Config.get_logs_dir()
    args = {
        'logs_dir': dirpath,
        'spider_child': CHILD_GOODS_LIST_RANKING,
        'log_id': "",  # "39"
    }
    Spider.crawl(NAME_AMAZON, spider_args=args)
