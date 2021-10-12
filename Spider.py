from scrapy import cmdline
from pyscrapy.spiders import GympluscoffeeSpider
from Config import Config
from service import DB
from pyscrapy.models import Table


class Spider:

    @staticmethod
    def crawl(name: str = GympluscoffeeSpider.name, output=None):
        dirpath = Config.get_logs_dir()
        cmd_list = ['scrapy', 'crawl', name, '-a', 'logs_dir='+dirpath]
        if output:
            # 输出爬虫结果到文件
            cmd_list.extend(['-o', output])
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
    Spider.crawl(GympluscoffeeSpider.name)
