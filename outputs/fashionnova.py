import time
from pyscrapy.models import Goods, RankingGoods, RankingLog, GoodsReview, SpiderRunLog
from outputs import SheinOutput
import json


class FashionnovaOutput(SheinOutput):
    site_name = 'fashionnova'


    def __init__(self, run_log: SpiderRunLog):
        super(FashionnovaOutput, self).__init__(run_log)

    def output_top_100(self):
        sheet = self.work_sheet
        log = self.ranking_log_model
        if not log:
            raise RuntimeError('找不到排行榜数据')
        db_session = self.db_session
        ranking_goods_list = db_session.query(RankingGoods).filter_by(**{'ranking_log_id': log.id}).order_by(
            RankingGoods.rank_num.asc()).all()
        current_time = int(time.time())
        month_in_12 = current_time - 3600 * 24 * 365
        month_in_6 = current_time - 3600 * 24 * 180
        month_in_3 = current_time - 3600 * 24 * 90
        month_in_2 = current_time - 3600 * 24 * 60
        month_in_1 = current_time - 3600 * 24 * 30
        week_in_1 = current_time - 3600 * 24 * 7

        title_row = ('ID', '图片', '排名', 'code', '商品标题', '商品链接', '更新时间',
                     '价格/US$', '1年内评论', '6个月内评论数', '3个月内评论数', '2个月内评论', '1个月内评论', '1周内评论', '总评论数')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_row_index = 2

        for rgoods in ranking_goods_list:
            goods = Goods.get_model(db_session, {'id': rgoods.goods_id})

            details = json.loads(goods.details)
           
            image = self.get_image_info(goods.local_image) if goods.local_image else ''
           
            updated_at = self.timestamp_to_str(goods.updated_at)
            brand = details['brand'] if 'brand' in details else ''
            sku_num = 1
            if 'relation_colors' in details:
                relation_colors = details['relation_colors']
                if relation_colors:
                    sku_num += len(relation_colors)

            reviews_month_12 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > month_in_12).count()
            reviews_month_6 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > month_in_6).count()
            reviews_month_3 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > month_in_3).count()
            reviews_month_2 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > month_in_2).count()
            reviews_month_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > month_in_1).count()
            reviews_week_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_code == goods.code, GoodsReview.review_time > week_in_1).count()

            goods_col_index = 1
            goods_info_list = [
                goods.id, image, rgoods.rank_num, goods.code,
                goods.title, goods.url, updated_at, goods.price, reviews_month_12, reviews_month_6, reviews_month_3,
                reviews_month_2, reviews_month_1, reviews_week_1,  goods.reviews_num
            ]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)

    def output(self):
        self.output_top_100()

