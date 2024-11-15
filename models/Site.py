from sqlalchemy import Column, String, Integer, Float, Text, Boolean
from . import BaseModel

# TODO ID 雪花算法
class Site(BaseModel):

    __tablename__ = BaseModel.table_prefix + 'sites' + BaseModel.table_suffix
    
    name = Column(String(64), default='gympluscoffee', comment='网站名')
    domain = Column(String(64), default='gympluscoffee.com', comment='域名')
    home_url = Column(String(128), default='https://gympluscoffee.com/', comment='网站首页')
    custom_short_name = Column(String(64), default='', comment='客户简称')
    state = Column(Boolean, default=True)