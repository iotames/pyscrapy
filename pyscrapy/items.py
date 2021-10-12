# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GympluscoffeeItem(scrapy.Item):
    goods_title = scrapy.Field()
    goods_url = scrapy.Field()


class PyscrapyItem(scrapy.Item):
    print('========start==PyscrapyItem===process_item===')
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
