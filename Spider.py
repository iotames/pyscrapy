from scrapy import cmdline
from pyscrapy.spiders.gympluscoffee import GympluscoffeeSpider
from Config import Config


class Spider:

    @staticmethod
    def crawl(name: str = GympluscoffeeSpider.name, output=None):
        dirpath = Config.get_logs_dir()
        cmd_list = ['scrapy', 'crawl', name, '-a', 'logs_dir='+dirpath]
        if output:
            # 输出爬虫结果到文件
            cmd_list.extend(['-o', output])
        cmdline.execute(cmd_list)


if __name__ == '__main__':
    Spider.crawl(GympluscoffeeSpider.name, Config.ROOT_PATH + '/runtime/spider.csv')
