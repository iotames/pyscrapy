from scrapy import cmdline
from pyscrapy.spiders import GympluscoffeeSpider, StrongerlabelSpider, AmazonSpider, SheinSpider
from Config import Config
from service import DB
from pyscrapy.models import Table


class Spider:

    @staticmethod
    def crawl(name: str = GympluscoffeeSpider.name, output=None, spider_args=None):

        cmd_list = ['scrapy', 'crawl', name]
        if output:
            # 输出爬虫结果到文件
            cmd_list.extend(['-o', output])
        if spider_args:
            for key, value in spider_args.items():
                cmd_list.extend(['-a', key + "=" + value])
        cmdline.execute(cmd_list)

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
        'spider_child': SheinSpider.CHILD_GOODS_DETAIL_TOP_REVIEWS,
        'log_id': "",  # "39"
    }
    Spider.crawl('shein', spider_args=args)
