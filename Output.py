# from outputs import EydaOutput
from outputs import AimnOutput, SweatybettyOutput, StrongerlabelOutput, SheinOutput, FashionnovaOutput, AmazonOutput, KindredbravelyOutput, MyproteinOutput, EydaOutput, AloyogaOutput
from pyscrapy.models import SpiderRunLog, GoodsReview


if __name__ == '__main__':
    # ot = EydaOutput()
    # ot.output()

    db_session = SpiderRunLog.get_db_session()

    log = SpiderRunLog.get_model(db_session, {'id': 41})  # 6 15 16
    # FashionnovaOutput(log).output()
    # AmazonOutput(log).output()
    # StrongerlabelOutput(log).output()
    # KindredbravelyOutput().output()
    # MyproteinOutput().output()
    SweatybettyOutput().output_to_excel()
    # EydaOutput().output()
    # AloyogaOutput().output()
