# from outputs import EydaOutput
from outputs import StrongerlabelOutput, SheinOutput
from pyscrapy.models import SpiderRunLog, GoodsReview


if __name__ == '__main__':
    # ot = EydaOutput()
    # ot.output()

    db_session = SpiderRunLog.get_db_session()

    # log = SpiderRunLog.get_model(db_session, {'id': 26})  # 6 15 16
    # SheinOutput(log).output()

    reviews = GoodsReview.get_all_model(db_session, {"goods_spu": "w21062176471"})
    print(len(reviews))
    # for review in reviews:
    #     print(review.time_str)

    # StrongerlabelOutput(log).output()