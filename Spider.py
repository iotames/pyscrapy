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
        db = DB.get_instance(config.get_database())
        db.ROOT_PATH = config.ROOT_PATH
        engine = db.get_db_engine()
        Table.create_all_tables(engine)


if __name__ == '__main__':
    # Spider.create_all_tables()

    dirpath = Config.get_logs_dir()
    args = {
        'logs_dir': dirpath,
        # 'spider_child': CHILD_GOODS_LIST_STORE_PAGE,
        'spider_child': CHILD_GOODS_LIST,
        'log_id': "",  # "39"
        'input_args': {
            # "store_name": "Baleaf",
            # "code": "Baleaf_Yoga_Women_s_Tops",
            # "url": "https://www.amazon.com/stores/page/E056317A-063C-4669-AF0B-964CD6C4A06F",
            # "group_log_id": 5
            # "code": "Baleaf_Women"
            # "ranking_log_id": 20,
            # 'category_name': "Tennisröcke für Damen",
            # Women's Running Shorts: https://www.amazon.com/bestsellers/fashion/2371114011
            # Women's Tennis Skorts: https://www.amazon.com/bestsellers/fashion/2371145011 https://www.amazon.com/Best-Sellers-Clothing-Shoes-Jewelry-Skorts/zgbs/fashion/2371145011/ref=zg_bs_nav_fashion_5_2371144011
            # Women's Outdoor Recreation Shirts: https://www.amazon.com/bestsellers/sporting-goods/11443924011 https://www.amazon.com/gp/bestsellers/sporting-goods/11443924011/ref=pd_zg_hrsr_sporting-goods
            # Tennisröcke für Damen https://www.amazon.de/bestsellers/sports/3771963031 https://www.amazon.de/gp/bestsellers/sports/3771963031/ref=pd_zg_hrsr_sports
            # 'url': 'https://www.amazon.de/bestsellers/sports/3771963031'
        }
    }
    Spider.crawl(NAME_ALIEXPRESS, spider_args=args)
