import time
from pyscrapy.models import Goods, RankingGoods, RankingLog, GoodsReview
from outputs.baseoutput import BaseOutput
import json


class SheinOutput(BaseOutput):
    site_name = 'shein'
    rank_category: str

    def __init__(self, filename=None):
        if not filename:
            filename = self.site_name
        super(SheinOutput, self).__init__('商品明细', filename)

    def get_ranking_log(self, category_name: str):
        db_session = RankingLog.get_db_session()
        return RankingLog.get_log(db_session, self.site_id, category_name)

    def output_top_100(self):
        sheet = self.work_sheet
        log = self.get_ranking_log(self.rank_category)
        if not log:
            raise RuntimeError('找不到排行榜数据')
        if time.time() - log.created_at > 3600 * 72:
            raise RuntimeError('最近排行榜数据已超过72小时, 请重新采集')
        db_session = self.db_session
        ranking_goods_list = RankingGoods.get_all_model(db_session, {'ranking_log_id': log.id})
        current_time = int(time.time())
        month_in_3 = current_time - 3600 * 24 * 90
        month_in_2 = current_time - 3600 * 24 * 60
        month_in_1 = current_time - 3600 * 24 * 30
        week_in_1 = current_time - 3600 * 24 * 7

        title_row = ('ID', '图片', '排名', '首评时间', 'goods_id', 'SPU', '颜色', '品类', '商品标题', '商品链接', '更新时间',
                     '价格/US$', '3个月内评论数', '2个月内评论', '1个月内评论', '1周内评论', '所属品牌', 'SKU数', '总评论数')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_row_index = 2

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
                GoodsReview.goods_id == goods.id, GoodsReview.review_time > month_in_3).count()
            reviews_month_2 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_id == goods.id, GoodsReview.review_time > month_in_2).count()
            reviews_month_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_id == goods.id, GoodsReview.review_time > month_in_1).count()
            reviews_week_1 = db_session.query(GoodsReview).filter(
                GoodsReview.goods_id == goods.id, GoodsReview.review_time > week_in_1).count()

            goods_col_index = 1
            goods_info_list = [
                goods.id, image, rgoods.rank_num, first_at, goods.code, goods.asin, color, goods.category_name,
                goods.title, goods.url, updated_at, goods.price, reviews_month_3, reviews_month_2, reviews_month_1,
                reviews_week_1, brand, sku_num, goods.reviews_num
            ]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('ID', '图片', '排名', '上架时间（首个评论）', 'goods_id', 'SPU', '颜色', '品类', '商品标题', '商品链接', '更新时间',
                     '价格/US$', '评论数', '销量(评论*20)', '销售额(估算)', '所属品牌', 'SKU数', '1星评论数', '2星评论数', '3星评论数',
                     '4星评论数', '5星评论数', '颜色销量')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id, Goods.reviews_num > 0).all()
        goods_row_index = 2

        for goods in goods_list:
            # 商品信息元组
            goods_col_index = 1
            details = json.loads(goods.details)
            updated_at = self.timestamp_to_str(goods.updated_at)
            first_at = ''
            if 'first_review_time' in details:
                first_at = details['first_review_time']
            image = ''
            if goods.local_image:
                image = self.get_image_info(goods.local_image)

            brand = details['brand'] if 'brand' in details else ''
            spu = details['spu'] if 'spu' in details else ''
            goods_id = details['goods_id'] if 'goods_id' in details else ''
            color = details['color'] if 'color' in details else ''
            rank_score = details['rank_score']
            relation_colors = details['relation_colors']
            sku_num = 1
            if relation_colors:
                sku_num += len(relation_colors)
            category_name = goods.category_name
            goods_url = goods.url
            reviews_num = goods.reviews_num
            rank_num = details['rank_num'] if 'rank_num' in details else 0
            if not rank_num:
                rank_num = details['rank_in'] if 'rank_in' in details else 0

            goods_info_list = [
                goods.id, image, rank_num, first_at, goods_id, spu, color, category_name, goods.title, goods_url, updated_at,
                goods.price, reviews_num, reviews_num*20, reviews_num*20*goods.price, brand, sku_num, rank_score["1"],
                rank_score["2"], rank_score["3"], rank_score["4"], rank_score["5"]
            ]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = SheinOutput()
    ot.rank_category = "Women Sports Tees & Tanks"  # "Women Sports Leggings"  # "Women Activewear"
    ot.output_top_100()
    # db_session = RankingGoods.get_db_session()
    # rank_goods_list = RankingGoods.get_all_model(db_session, {'site_id': 1})
    # total_reviews_num = 0
    # for rgoods in rank_goods_list:
    #     goods = Goods.get_model(db_session, {'id': rgoods.goods_id})
    #     rgoods.reviews_num = goods.reviews_num
    #     total_reviews_num += goods.reviews_num
    # db_session.commit()
    # print(total_reviews_num)

