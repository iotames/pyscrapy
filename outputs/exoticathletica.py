from pyscrapy.models import SpiderRunLog
from outputs.strongerlabel import StrongerlabelOutput
from pyscrapy.enum.spider import *


class ExoticathleticaOutput(StrongerlabelOutput):

    site_name = NAME_EXOTICATHLETICA

    quantity_map = {}
    run_log: SpiderRunLog

    def __init__(self, run_log: SpiderRunLog):
        super(ExoticathleticaOutput, self).__init__(run_log)


if __name__ == '__main__':
    db_session = SpiderRunLog.get_db_session()
    log = SpiderRunLog.get_model(db_session, {'id': 2})
    sl = ExoticathleticaOutput(log)
    sl.output()
