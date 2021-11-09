from pyscrapy.models import Site
from api.BaseController import BaseController
import time


class SpiderController(BaseController):

    def get_spiders_list(self) -> list:
        sites = self.db_session.query(Site).all()
        data = []
        for site in sites:
            data.append({"id": site.id, "name": site.name, "home_url": site.home_url,
                         "created_at": time.strftime("%Y%m%d %H:%M", time.localtime(site.created_at))})
        return data
