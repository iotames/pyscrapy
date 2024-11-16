from email.policy import default
from sqlalchemy import Column, String, Integer, Text, DateTime, BigInteger, JSON
from . import BaseModel, UrlRequestSnapshot
from datetime import datetime
from scrapy import Request
import hashlib


class UrlRequest(BaseModel):

    __tablename__ = BaseModel.table_prefix + 'url_request' + BaseModel.table_suffix

    site_id = Column(BigInteger, default=0, nullable=False)
    request_hash = Column(String(64), nullable=False, unique=True)
    url = Column(String(5000), nullable=False)
    method = Column(String(32), nullable=False)
    status_code = Column(Integer, nullable=False)
    request_body = Column(Text, nullable=False)
    request_headers = Column(JSON, nullable=False)
    response_headers = Column(JSON, nullable=False)
    step = Column(Integer, default=0, nullable=False)
    start = Column(Integer, default=0, nullable=False)
    group = Column(Integer, default=0, nullable=False)
    data_format = Column(JSON, nullable=False)
    data_raw = Column(Text, nullable=False)
    collected_at = Column(DateTime, default=None)

    # # 定义唯一索引
    # __table_args__ = (
    #     {'postgresql_indexes': [
    #         {'name': 'UQE_ods_cwr_end_url_request_nd_id', 'columns': ['id'], 'unique': True},
    #         {'name': 'UQE_ods_cwr_end_url_request_nd_request_hash', 'columns': ['request_hash'], 'unique': True}
    #     ]}
    # )

    def setDataFormat(self, data):
        self.data_format = data
    
    def setDataRaw(self, data: str):
        self.data_raw = data
        
    def save(self, startAt):
        if self.id is None or self.id == 0:
            self.get_db_session().add(self)
        else:
            data = {'data_format': str(self.data_format), 'data_raw':self.data_raw, 'collected_at':datetime.now()}
            print("---------UrlRequest------save-----", data)
            self.get_db_session().query(UrlRequest).filter(UrlRequest.request_hash==self.request_hash).update(data)
        self.get_db_session().commit()
        UrlRequestSnapshot.create_url_request_snapshot(self, startAt, self.status_code)

    @classmethod
    def getbyRequestHash(cls, requestHash: str):
        return cls.get_self(dict(request_hash=requestHash))
    
    @classmethod
    def getByRequest(cls, request: Request) -> 'UrlRequest':
        return cls.getbyRequestHash(cls.get_request_hash(request.method, request.url, request.body))

    @staticmethod
    def get_request_hash(method, url, request_body):
        method = method.upper()
        shastr = method + url
        if method == "POST":
            shastr += request_body.strip()
        return get_sha256(shastr)
    
    @classmethod
    def createUrlRequest(cls, request:Request, siteid: int, step, start, group: int) -> 'UrlRequest':
        new_record = cls(
            site_id=siteid,
            request_hash=cls.get_request_hash(request.method, request.url, request.body),
            url=request.url,
            method=request.method.upper(),
            status_code=200,
            request_body=request.body,
            request_headers=request.headers,
            step=step,
            start=start,
            group=group,
            collected_at=datetime.now()
        )
        return new_record

def get_sha256(s):
    h = hashlib.sha256()
    h.update(s.encode('utf-8'))
    return h.hexdigest()