from pyscrapy.models import SpiderRunLog
from outputs.strongerlabel import StrongerlabelOutput
from pyscrapy.enum.spider import *


class ParagonfitwearOutput(StrongerlabelOutput):

    site_name = NAME_PARAGONFITWEAR

    def __init__(self, run_log: SpiderRunLog):
        super(ParagonfitwearOutput, self).__init__(run_log)


if __name__ == '__main__':
    db_session = SpiderRunLog.get_db_session()
    log = SpiderRunLog.get_model(db_session, {'id': 18})
    sl = ParagonfitwearOutput(log)
    sl.output()
