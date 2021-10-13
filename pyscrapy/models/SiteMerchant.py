from sqlalchemy import Column, String, Integer
from . import BaseModel


class SiteMerchant(BaseModel):

    __tablename__ = 'site_merchant'

    id = Column(Integer, primary_key=True)
    code = Column(String(32))
    site_id = Column(Integer, comment='所属网站')
    url = Column(String(255))
    name = Column(String(64), comment='商户名')
