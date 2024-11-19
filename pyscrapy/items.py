# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field

class FromPage:
    FROM_PAGE_HOME = "page_home"
    FROM_PAGE_PRODUCT_DETAIL = "page_product_detail"
    FROM_PAGE_PRODUCT_REVIEWS = "page_product_reviews"
    FROM_PAGE_PRODUCT_QUANTITY = "page_product_quantity"
    FROM_PAGE_PRODUCT_LIST = "page_product_list"
    
class PyscrapyItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class BaseProductItem(Item):
    NOT_SAVE_FILEDS = ['image_urls', 'image_paths', 'UrlRequest', 'FromKey', 'SkipRequest', 'StartAt', 'DataRaw']
    DataRaw = Field()
    StartAt = Field()
    SkipRequest = Field()
    UrlRequest = Field()
    FromKey = Field()
    SizeNum = Field()
    SizeList = Field()
    Thumbnail = Field()
    Image = Field()
    Url = Field()
    Title = Field()
    Color = Field()
    OldPriceText = Field()
    OldPrice = Field()
    PriceText = Field()
    FinalPrice = Field()
    Category = Field()
    TotalInventoryQuantity = Field()
    Material= Field()
    Description = Field()
    PublishedAt = Field()
    Tags = Field()
    
    image_urls = Field()
    image_paths = Field()
    
    # model = Field()
    # category_name = Field()
    # category_id = Field()

    # code = Field()
    # spu = Field()

    # status = Field()
    # title = Field()
    # url = Field()
    # original_price = Field()
    # price = Field()
    # price_text = Field()
    # image = Field()
    # detail = Field()
    # variants_num = Field()
    # reviews_num = Field()
    # sales_num = Field()
    # quantity = Field()
    # collected_at = Field()
    
    # local_image = Column(String(255), comment='本地图片地址')
    # sales_num_last_month = Column(Integer, default=0, comment='上月销量')
