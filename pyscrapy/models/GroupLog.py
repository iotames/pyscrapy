from sqlalchemy import Column, String, Integer, DateTime
from . import BaseModel
from sqlalchemy import and_


class GroupLog(BaseModel):

    __tablename__ = 'group_log'

    site_id = Column(Integer, default=0)
    # rank_type = Column(Integer, comment='排序方式', default=0)
    # category_id = Column(Integer, comment='排名分类ID', default=0)
    # category_code = Column(String(64), comment='分类code')
    # category_name = Column(String(64), comment='分类名')
    group_type = Column(Integer, comment='分组类别', default=0)
    title = Column(String(128), comment='分组标题')
    code = Column(String(128), comment='分组编码')
    remark = Column(String(255), comment='备注')
    url = Column(String(255))
    log_date = Column(DateTime, comment='记录日期')
    parent_id = Column(Integer, default=0)
    link_id = Column(String(128), comment='连接ID')

    @classmethod
    def get_log(cls, db_session, site_id: int, code: str, rank_type=0):
        return db_session.query(cls).filter(and_(
            cls.site_id == site_id,
            cls.code == code,
            cls.rank_type == rank_type
        )).order_by(cls.created_at.desc()).first()

    @classmethod
    def get_log_by_id(cls, db_session, log_id: int):
        return db_session.query(cls).filter(cls.id == log_id).first()

