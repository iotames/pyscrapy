from sqlalchemy import Column, String, Integer, Text, DateTime, BigInteger, JSON, Numeric
from . import BaseModel, UrlRequest
from datetime import datetime

class UrlRequestSnapshot(BaseModel):
    
    __tablename__ = BaseModel.table_prefix + 'url_request_snapshot' + BaseModel.table_suffix
    
    site_id = Column(BigInteger, default=0, nullable=False)
    request_hash = Column(String(64), nullable=False)
    data_format = Column(JSON, nullable=False)
    data_raw = Column(Text, nullable=False)
    start_at = Column(DateTime, default=None)
    end_at = Column(DateTime, default=None)
    cost_time = Column(Numeric(8, 6), default=0, nullable=False)
    status = Column(Integer, nullable=False)
    create_date = Column(String(32), nullable=False)

    # # 定义索引
    # __table_args__ = (
    #     {'postgresql_indexes': [
    #         {'name': 'IDX_ods_cwr_end_url_request_snapshot_nd_request_hash', 'columns': ['request_hash']},
    #         {'name': 'UQE_ods_cwr_end_url_request_snapshot_nd_id', 'columns': ['id'], 'unique': True}
    #     ]}
    # )

    @classmethod
    def create_url_request_snapshot(cls, ur: UrlRequest, start_at, status):
        m = UrlRequestSnapshot(
            site_id=ur.site_id,
            request_hash=ur.request_hash,
            data_format=ur.data_format,
            data_raw=ur.data_raw,
            # cost_time=None,
            # start_at=None,
            # end_at=None,
            # status=None,
            # create_date=None
        )

        if m.site_id == 0 or m.request_hash == "" or not m.data_format:
            print(f"-----------ur.url={ur.url}")
            raise ValueError(f"UrlRquestSnapshot参数不完整--m.siteID({m.site_id})--ur.RequestHash({m.request_hash})---ur.DataFormat({m.data_format})")

        cost_sec = (datetime.now() - start_at).total_seconds()
        if cost_sec > 99:
            cost_sec = 99

        ntime = datetime.now()
        m.cost_time = cost_sec
        m.start_at = start_at
        m.end_at = ntime
        m.status = status
        m.create_date = ntime.strftime("%Y%m%d")
        try:
            db_session = cls.get_db_session()
            db_session.add(m)
            db_session.commit()
        except Exception as e:
            raise e