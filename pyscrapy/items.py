# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class PyscrapyItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class BaseProductItem(Item):
    image_urls = Field()
    image_paths = Field()
    model = Field()

    spider_name = Field()
    category_name = Field()
    category_id = Field()

    code = Field()
    spu = Field()

    status = Field()
    title = Field()
    url = Field()
    original_price = Field()
    price = Field()
    price_text = Field()
    image = Field()
    detail = Field()
    variants_num = Field()
    reviews_num = Field()
    sales_num = Field()
    quantity = Field()
    collected_at = Field()
    # local_image = Column(String(255), comment='本地图片地址')
    # sales_num_last_month = Column(Integer, default=0, comment='上月销量')
