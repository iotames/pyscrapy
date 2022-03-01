import time
from pyscrapy.models import Goods, RankingGoods, RankingLog, GoodsReview, SpiderRunLog
from outputs.baseoutput import BaseOutput
import json


class SheinMultiOutput(BaseOutput):
    site_name = 'shein'
    rank_category: str

    def __init__(self):
        self.rank_category = "shein202203"
        filename = "{}_{}".format(self.site_name, self.rank_category).replace(' ', '_').replace("'", "-").replace("&", "and")
        self.download_filename = "{}_{}.xlsx".format(filename, str(1))
        super(SheinMultiOutput, self).__init__('商品信息列表', filename)

    def output_top_100(self):
        if self.is_download_file_exists():
            return True
        sheet = self.work_sheet

        db_session = self.db_session
        rank_logs = db_session.query(RankingLog).all()
        ranking_goods_list = []
        for rank_log in rank_logs:
            r_goods_list = db_session.query(RankingGoods).filter_by(**{'ranking_log_id': rank_log.id}).order_by(RankingGoods.rank_num.asc()).all()
            for gd in r_goods_list:
                ranking_goods_list.append(gd)

        title_row = ('ID', '图片', '排名', '首评时间', 'goods_id', 'SPU', '颜色', '品类', '商品标题', '商品链接', '更新时间', '价格/US$',
                     '3个月内评论数', '2个月内评论', '1个月内评论', '1周内评论',
                     '所属品牌', 'SKU数', '总评论数')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_row_index = 2

        current_time = int(time.time())
        month_in_3 = current_time - 3600 * 24 * 90
        month_in_2 = current_time - 3600 * 24 * 60
        month_in_1 = current_time - 3600 * 24 * 30
        week_in_1 = current_time - 3600 * 24 * 7

        for rgoods in ranking_goods_list:
            goods = Goods.get_model(db_session, {'id': rgoods.goods_id})
            details = json.loads(goods.details)
            first_at = details['first_review_time'] if 'first_review_time' in details else ''
            image = self.get_image_info(goods.local_image) if goods.local_image else ''
            color = details['color'] if 'color' in details else ''
            updated_at = self.timestamp_to_str(goods.updated_at)
            brand = details['brand'] if 'brand' in details else ''
            sku_num = 1
            if 'relation_colors' in details:
                relation_colors = details['relation_colors']
                if relation_colors:
                    sku_num += len(relation_colors)

            reviews_month_3 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_spu == goods.asin, GoodsReview.review_time > month_in_3).count()
            reviews_month_2 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_spu == goods.asin, GoodsReview.review_time > month_in_2).count()
            reviews_month_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_spu == goods.asin, GoodsReview.review_time > month_in_1).count()
            reviews_week_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_spu == goods.asin, GoodsReview.review_time > week_in_1).count()

            goods_col_index = 1
            goods_info_list = [
                goods.id, image, rgoods.rank_num, first_at, goods.code, goods.asin, color, goods.category_name,
                goods.title, goods.url, updated_at, goods.price,
                reviews_month_3, reviews_month_2, reviews_month_1, reviews_week_1,
                brand, sku_num, goods.reviews_num
            ]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)
        # TODO BUG： 通过API接口下载和通过本入口生成的EXCEL， 文件内容不一样。
        # self.copy_to_download_path(self.output_file)

    def output(self):
        self.output_top_100()


if __name__ == '__main__':
    # db_session = SpiderRunLog.get_db_session()
    # log = SpiderRunLog.get_model(db_session, {'id': 25})  # 24 25
    ot = SheinMultiOutput()
    ot.output()


