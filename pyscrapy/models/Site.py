from sqlalchemy import Column, String, Integer, Float, Text
from . import BaseModel


class Site(BaseModel):

    __tablename__ = 'site'
    name = Column(String(64), default='gympluscoffee', comment='网站名')
    domain = Column(String(64), default='gympluscoffee.com', comment='域名')
    home_url = Column(String(128), default='https://gympluscoffee.com/', comment='网站首页')
