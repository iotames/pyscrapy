# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from scrapy import Item, Field


class GympluscoffeeCategoryItem(Item):
    site_id = Field()
    model = Field()
    parent_name = Field()
    parent_url = Field()
    name = Field()
    url = Field()


class GympluscoffeeGoodsItem(Item):
    image_urls = Field()
    images = Field()
    image_paths = Field()
    model = Field()

    site_id = Field()
    code = Field()
    title = Field()
    url = Field()
    image = Field()
    category_id = Field()
    category_name = Field()
    status = Field()
    price = Field()
    details = Field()
    reviews_num = Field()


class GympluscoffeeGoodsSkuItem(Item):
    image_urls = Field()
    images = Field()
    image_paths = Field()
    model = Field()

    site_id = Field()
    code = Field()
    goods_id = Field()
    category_id = Field()
    category_name = Field()
    options = Field()  # option1 option2 option3
    title = Field()  # sku
    full_title = Field()  # name
    price = Field()
    inventory_quantity = Field()
    barcode = Field()
    image = Field()


class StrongerlabelGoodsItem(Item):
    image_urls = Field()
    images = Field()
    image_paths = Field()

    code = Field()  # id
    title = Field()
    url = Field()
    quantity = Field()  # quantity inventory_quantity
    categories = Field()
    created_at = Field()
    stickers = Field()  # { in-stock: true, out-of-stock: false}
    price = Field()
    image = Field()


class PyscrapyItem(Item):
    # print('========start==PyscrapyItem===process_item===')
    # define the fields for your item here like:
    # name = Field()
    pass
