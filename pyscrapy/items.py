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


class StrongerlabelGoodsItem(scrapy.Item):
    code = scrapy.Field()  # id
    title = scrapy.Field()
    url = scrapy.Field()
    quantity = scrapy.Field()  # quantity inventory_quantity
    categories = scrapy.Field()
    created_at = scrapy.Field()
    stickers = scrapy.Field()  # { in-stock: true, out-of-stock: false}
    price = scrapy.Field()
    image = scrapy.Field()


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
