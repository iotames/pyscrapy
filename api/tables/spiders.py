from api.tables.base import Base


class Spiders(Base):

    name = "spiders"

    @property
    def columns(self):
        cols = super().columns.copy()
        append_cols = [
            {'name': 'name', 'attributes': {'title': '爬虫名', 'width': '160'}},
            {'name': 'home_url', 'attributes': {'title': '网站首页', 'width': '280'}},
        ]
        cols.extend(append_cols)
        return cols


class SpiderRunLogs(Base):
    name = "spider_run_logs"

    @property
    def columns(self):
        cols = super().columns.copy()
        append_cols = [
            {'name': 'spider_name', 'attributes': {'title': '爬虫名', 'width': '160'}},
            {'name': 'spider_child', 'attributes': {'title': '任务类型', 'width': '180'}},
            {'name': 'status', 'attributes': {'title': '状态', 'width': '100'}},
        ]
        cols.extend(append_cols)
        return cols
