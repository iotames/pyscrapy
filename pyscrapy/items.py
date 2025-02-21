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

    Code = Field()
    Spu = Field()
    MadeIn = Field()
    UrlKey = Field()
    Gender = Field()
    Brand = Field()
    ColorNum = Field()
    SizeNum = Field()
    SkuNum = Field()
    Variants = Field()
    SizeList = Field()
    Thumbnail = Field()
    Image = Field()
    Url = Field()
    Title = Field()
    SubTitle = Field()
    Color = Field()
    OldPriceText = Field()
    OldPrice = Field()
    PriceText = Field()
    FinalPrice = Field()
    Discount = Field()
    ParentGroup = Field()
    GroupName = Field()
    Category = Field()
    CategoryUrl = Field()
    PageIndex = Field()
    TotalInventoryQuantity = Field()
    TotalReviewsText = Field()
    TotalReviews = Field()
    ReviewRating = Field()
    Material= Field()
    Description = Field()
    PublishedAt = Field()
    Tags = Field()
    
    image_urls = Field()
    image_paths = Field()
    # failed_urls = Field()
    
    # reviews_num = Field()
    # sales_num = Field()
    # quantity = Field()
    # collected_at = Field()
