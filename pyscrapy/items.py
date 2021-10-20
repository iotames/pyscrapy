# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from pyscrapy.models import BaseModel


class GympluscoffeeCategoryItem(scrapy.Item):
    site_id = scrapy.Field()
    model = scrapy.Field()
    parent_name = scrapy.Field()
    parent_url = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()


class GympluscoffeeGoodsItem(scrapy.Item):
    site_id = scrapy.Field()
    model = scrapy.Field()
    code = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    category_id = scrapy.Field()
    category_name = scrapy.Field()
    status = scrapy.Field()


class GympluscoffeeGoodsSkuItem(scrapy.Item):
    site_id = scrapy.Field()
    model = scrapy.Field()
    code = scrapy.Field()
    goods_id = scrapy.Field()
    category_id = scrapy.Field()
    category_name = scrapy.Field()
    options = scrapy.Field()  # option1 option2 option3
    title = scrapy.Field()  # sku
    full_title = scrapy.Field()  # name
    price = scrapy.Field()
    inventory_quantity = scrapy.Field()
    barcode = scrapy.Field()
    image = scrapy.Field()


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





class PyscrapyItem(scrapy.Item):
    # print('========start==PyscrapyItem===process_item===')
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
