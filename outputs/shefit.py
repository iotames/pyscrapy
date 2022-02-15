from pyscrapy.models import Goods, GoodsReview
from outputs.baseoutput import BaseOutput
import json


class ShefitOutput(BaseOutput):

    site_name = 'shefit'

    def __init__(self):
        super(ShefitOutput, self).__init__('商品信息列表', self.site_name)
        self.get_trans_dic_all()

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'code', '图片', '分类', '商品标题', '商品链接', '更新时间', '价格/$', '状态', '库存', '库存详情')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        goods_row_index = 2
        sheet_reviews = self.wb.create_sheet(title='评论详情', index=1)
        details_title_row = ('时间', '星级', '款式', '体型', '年龄', 'activity', '标题', '详情')
        sheet_reviews.append(details_title_row)

        for goods in goods_list:
            goods_col_index = 1
            time_str = self.timestamp_to_str(goods.updated_at, "%Y-%m-%d %H:%M")
            # 商品信息元组
            image = self.get_image_info(goods.local_image) if goods.local_image else ''
            details = json.loads(goods.details) if goods.details else {"sku_list": []}

            goods_url = goods.url
            sku_text = ''
            for sku_info in details['sku_list']:
                sku_text += sku_info['name'] + " : " + str(sku_info['quantity']) + "\n"
            goods_info_list = [
                goods.id, goods.code, image, goods.category_name, goods.title, goods_url, time_str, goods.price,
                Goods.statuses_map[goods.status], goods.quantity, sku_text
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            self.output_reviews(sheet_reviews, goods.id)
            goods_row_index += 1

        self.wb.save(self.output_file)

    def update_reviews_rows(self, reviews_rows_per: list, reviews_rows: list, reviews_list: list):
        # 多行数据批量转字符串
        reviews_rows_per_str = json.dumps(reviews_rows_per)
        reviews_rows_per_str_cn = self.to_chinese(reviews_rows_per_str, False)  # 多行数据批量翻译
        print(reviews_rows_per_str_cn)
        reviews_rows_per = json.loads(reviews_rows_per_str_cn)  # 多行数据字符串序列化为数组
        i = 0
        for review_row in reviews_rows_per:
            model = reviews_list[i]
            model.body_type = review_row["body_type"]
            model.activity = review_row["activity"]
            model.title = review_row['title']
            model.body = review_row['body']
            self.db_session.commit()
            i += 1
            reviews_rows.append(review_row)

    def output_reviews_only(self, goods_id: int):
        self.work_sheet.title = "评论详情"
        sheet_reviews = self.work_sheet
        details_title_row = ('时间', '星级', '款式', '体型', '年龄', 'activity', '标题', '详情')
        sheet_reviews.append(details_title_row)
        self.output_reviews(sheet_reviews, goods_id)
        self.wb.save(self.output_file)

    def output_reviews(self, sheet_reviews, goods_id):
        reviews = self.db_session.query(GoodsReview).filter(
            GoodsReview.site_id == self.site_id, GoodsReview.goods_id == goods_id).all()
        # reviews_rows = []
        # reviews_rows_per = []
        # reviews_list_per = []
        times = 0
        for review in reviews:
            times += 1
            # code = review.code
            rating = review.rating_value
            age = review.age
            time_text = review.time_str
            title = review.title
            body = review.body
            body_type = review.body_type
            activity = review.activity
            sku_text = review.sku_text

            # title = self.to_chinese(title, False)
            # review.title = title
            #
            # body_type = self.to_chinese(body_type)
            # review.body_type = body_type
            #
            # activity = self.to_chinese(activity)
            # review.activity = activity
            #
            # body = self.to_chinese(body, False)
            # review.body = body
            # self.db_session.commit()

            review_row = (time_text, rating, sku_text, body_type, age, activity, title, body)
            sheet_reviews.append(review_row)

            """
            reviews_rows_per.append(review_row)
            reviews_list_per.append(review)
            if times % 10 == 0:
                self.update_reviews_rows(reviews_rows_per, reviews_rows, reviews_list_per)
                reviews_rows_per = []
                reviews_list_per = []
            if times == len(reviews):
                self.update_reviews_rows(reviews_rows_per, reviews_rows, reviews_list_per)
            """

        # for review_row in reviews_rows:
        #     sheet_reviews.append(review_row)


if __name__ == '__main__':
    ot = ShefitOutput()
    ot.output()
    # ot.output_reviews_only(2)
    # print(ot.to_chinese("Running/walking/hiking, HIIT/Weightlifting/Gym, Yoga/Low intensity , Everyday Use, Other"))
