from pyscrapy.models import Goods, GoodsReview
from outputs.baseoutput import BaseOutput
import json
from translate import Translator
import requests


class ShefitOutput(BaseOutput):

    site_name = 'shefit'

    translator: Translator

    def __init__(self):
        super(ShefitOutput, self).__init__('商品信息列表', self.site_name)
        self.translator = Translator(to_lang='chinese', provider='mymemory')  # , proxies={'http': '127.0.0.1:1080'}

    def to_chinese(self, content: str):
        # return self.translator.translate(content)
        url = f"http://fanyi.youdao.com/translate?&doctype=json&type=AUTO&i={content}"
        response = requests.get(url)
        json_data = response.json()
        return json_data["translateResult"][0][0]["tgt"]

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
            goods_row_index += 1
        self.save_reviews()
        self.wb.save(self.output_file)

    def update_reviews_rows(self, reviews_rows_per: list, reviews_rows: list):
        reviews_rows_per_str = json.dumps(reviews_rows_per)
        reviews_rows_per_str_cn = self.to_chinese(reviews_rows_per_str)
        print(reviews_rows_per_str_cn)
        reviews_rows_per = json.loads(reviews_rows_per_str_cn)
        for review_row in reviews_rows_per:
            reviews_rows.append(review_row)

    def save_reviews(self):
        sheet_reviews = self.wb.create_sheet(title='评论详情', index=1)
        details_title_row = ('时间', '星级', '体型', '年龄', 'activity', '标题', '详情')
        sheet_reviews.append(details_title_row)
        reviews = self.db_session.query(GoodsReview).filter(GoodsReview.site_id == self.site_id).all()
        reviews_rows = []
        reviews_rows_per = []
        times = 0
        for review in reviews:
            times += 1
            # code = review.code
            body = review.body
            title = review.title
            # title = self.to_chinese(title)
            review.title = title
            body_type = review.body_type
            activity = review.activity
            rating = review.rating_value
            age = review.age
            time_text = review.time_str
            review_row = (time_text, rating, body_type, age, activity, title, body)
            # sheet_reviews.append(review_row)
            # self.db_session.commit()
            reviews_rows_per.append(review_row)
            if times % 10 == 0:
                self.update_reviews_rows(reviews_rows_per, reviews_rows)
                reviews_rows_per = []
            if times == len(reviews):
                self.update_reviews_rows(reviews_rows_per, reviews_rows)

        for review_row in reviews_rows:
            sheet_reviews.append(review_row)


if __name__ == '__main__':
    ot = ShefitOutput()
    ot.output()
    # print(ot.to_chinese("Running/walking/hiking, HIIT/Weightlifting/Gym, Yoga/Low intensity , Everyday Use, Other"))
