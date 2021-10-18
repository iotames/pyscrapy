from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput


class StrongerlabelOutput(BaseOutput):

    site_name = 'strongerlabel'

    def output(self):
        pass
        # goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        # for goods in goods_list:
        #     # www.strongerlabel.com/hk/
        #     goods.url = goods.url.replace('findify.bogus', 'www.strongerlabel.com')
        # self.db_session.commit()


if __name__ == '__main__':
    sl = StrongerlabelOutput()
    sl.output()
