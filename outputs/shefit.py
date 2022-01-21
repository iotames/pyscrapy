from pyscrapy.models import Goods, GoodsReview
from outputs.baseoutput import BaseOutput
import json
from translate import Translator


class ShefitOutput(BaseOutput):

    site_name = 'shefit'

    translator: Translator

    def __init__(self):
        super(ShefitOutput, self).__init__('商品信息列表', self.site_name)
        self.translator = Translator(to_lang='chinese', provider='mymemory')  # , proxies={'http': '127.0.0.1:1080'}

    def to_chinese(self, content: str):
        return self.translator.translate(content)

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
        self.wb.save(self.output_file)

    def test(self):
        reviews = self.db_session.query(GoodsReview).filter(Goods.site_id == self.site_id).all()
        trans_map = {}
        times = 0
        for review in reviews:
            if times > 0:
                break

            code = review.code
            body = review.body
            title = review.title
            body_type = review.body_type
            activity = review.activity
            age = review.age

            if code not in trans_map:
                trans_map[code] = dict(title=title, body=body, activity=activity, body_type=body_type)
        print(trans_map)
        # ak = json.dumps(trans_map)
        # sk = self.to_chinese(ak)
        # print(sk)
        # print(json.loads(sk))


if __name__ == '__main__':
    ot = ShefitOutput()
    # ot.output()
    ot.test()

