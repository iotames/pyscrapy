from pyscrapy.models import Site, SpiderRunLog, RankingLog
from outputs.baseoutput import BaseOutput
from api.BaseController import BaseController
from api.tables import Spiders as SpidersTable, SpiderRunLogs as SpiderRunLogsTable
from pyscrapy.enum.spider import get_children_list


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
                "children_list": get_children_list(site.name),
            })
        return data

    def get_spiders_run_logs(self, name, page=1, limit=10) -> dict:
        offset = (page - 1) * limit
        query = self.db_session.query(SpiderRunLog).filter(SpiderRunLog.spider_name == name)
        logs = query.order_by(
            SpiderRunLog.created_at.desc()).limit(limit).offset(offset).all()
        total = query.count()
        items = []
        for log in logs:
            row = {"id": log.id, "created_at": self.f_time(log.created_at),
                   "spider_name": log.spider_name,
                   "spider_child": log.spider_child,
                   "link_id": log.link_id,
                   "status": SpiderRunLog.STATUS_MAP[log.status]
                   }
            items.append(row)
        return dict(items=items, total=total)

    @staticmethod
    def get_table_columns(name: str) -> list:
        tables_cols = {
            SpidersTable.name: SpidersTable().columns,
            SpiderRunLogsTable.name: SpiderRunLogsTable().columns
        }
        return tables_cols[name]

    def output_excel_by_run_log_id(self, log_id: int) -> BaseOutput:
        run_log: SpiderRunLog = SpiderRunLog.get_model(self.db_session, {'id': log_id})
        if run_log.status != SpiderRunLog.STATUS_DONE:
            raise RuntimeError("爬虫运行结果异常")
        spider_name: str = run_log.spider_name
        class_name = spider_name.capitalize() + "Output"
        module = __import__("outputs")
        full_class = getattr(module, class_name)
        obj = full_class(run_log)
        # getattr(obj, "output")()
        return obj


if __name__ == '__main__':
    ctl = SpiderController()
    output = ctl.output_excel_by_run_log_id(53)
    print(output.output_file)
    print(output.download_filename)
