# from outputs import EydaOutput
from outputs import StrongerlabelOutput, SheinOutput
from pyscrapy.models import SpiderRunLog, GoodsReview


if __name__ == '__main__':
    # ot = EydaOutput()
    # ot.output()

    db_session = SpiderRunLog.get_db_session()

    log = SpiderRunLog.get_model(db_session, {'id': 51})  # 6 15 16
    SheinOutput(log).output()

    # StrongerlabelOutput(log).output()