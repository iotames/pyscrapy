# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GympluscoffeeGoodsItem(scrapy.Item):
    goods_title = scrapy.Field()
    goods_url = scrapy.Field()
    category_id = scrapy.Field()
    category_name = scrapy.Field()


class GympluscoffeeCategoryItem(scrapy.Item):
    site_id = scrapy.Field()
    parent_id = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()


class PyscrapyItem(scrapy.Item):
    # print('========start==PyscrapyItem===process_item===')
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
