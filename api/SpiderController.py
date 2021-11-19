from pyscrapy.models import Site, SpiderRunLog
from api.BaseController import BaseController
from api.tables import Spiders as SpidersTable, SpiderRunLogs as SpiderRunLogsTable


class SpiderController(BaseController):

    def get_spiders_list(self) -> list:
        sites = self.db_session.query(Site).all()
        data = []
        for site in sites:
            data.append({
                "id": site.id,
                "created_at": self.f_time(site.created_at),
                "name": site.name,
                "home_url": site.home_url,
            })
        return data

    def get_spiders_run_logs(self, name) -> list:
        logs = self.db_session.query(SpiderRunLog).filter(SpiderRunLog.spider_name == name).all()
        data = []
        for log in logs:
            row = {"id": log.id, "created_at": self.f_time(log.created_at),
                   "spider_name": log.spider_name, "status": SpiderRunLog.STATUS_MAP[log.status]
                   }
            data.append(row)
        return data

    @staticmethod
    def get_table_columns(name: str) -> list:
        tables_cols = {
            SpidersTable.name: SpidersTable().columns,
            SpiderRunLogsTable.name: SpiderRunLogsTable().columns
        }
        return tables_cols[name]

