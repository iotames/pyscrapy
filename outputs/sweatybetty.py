import json

from pyscrapy.models import Goods, GoodsSku, GoodsCategory
from outputs.baseoutput import BaseOutput
import time
# from translate import Translator
from openpyxl.drawing.image import Image
import os


class SweatybettyOutput(BaseOutput):

    site_name = 'sweatybetty'
    # translator: Translator
    categories: list

    def __init__(self):
        super(SweatybettyOutput, self).__init__('商品信息', self.site_name)
        self.categories = self.db_session.query(GoodsCategory).all()
        # self.translator = Translator(to_lang='chinese', provider='mymemory')

    # def to_chinese(self, content: str):
    #     return self.translator.translate(content)

    def get_image_info(self, path: str) -> dict:
        image_path = self.images_dir + os.path.sep + path
        image = {
            'type': Image,
            'path': image_path,
            'size': (100, 100)
        }
        return image

    def output_to_excel(self):
        sheet = self.work_sheet
        sheet.sheet_format.defaultRowHeight = 100
        # sheet.sheet_format.defaultColWidth = 100
        title_row = ('商品ID', '图片', '商品标题', '商品链接', '更新时间',
                     '评论数', '价格/CNY', '织物布料', '平均星级',
                     '5星评论', '4星评论', '3星评论', '2星评论', '1星评论')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        start_row_index = 2
        for goods in goods_list:
            time_tuple = time.localtime(goods.updated_at)
            time_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
            reviews_num = goods.reviews_num
            details = goods.details
            price = goods.price
            fabric = ''
            average, rating5, rating4, rating3, rating2, rating1 = (0, 0, 0, 0, 0, 0)
            if details:
                details = json.loads(details)
                if 'fabric' in details:
                    fabric = details['fabric']  # + " 翻译： " + self.to_chinese(details['fabric'])
                if reviews_num > 0:
                    rating = details['rating']
                    average = rating['average']
                    rating5 = rating['5']
                    rating4 = rating['4']
                    rating3 = rating['3']
                    rating2 = rating['2']
                    rating1 = rating['1']
            # 商品信息元组
            image = ''
            if goods.local_image:
                image = self.get_image_info(goods.local_image)
            goods_info_list = [goods.id, goods.title, goods.url, time_str,
                               reviews_num, price, fabric, average, rating5, rating4, rating3, rating2, rating1]
            goods_row_info = goods_info_list.copy()
            goods_row_info.insert(1, image)

            self.set_values_to_row(sheet, goods_row_info, start_row_index)
            start_row_index += 1

        self.wb.save(self.output_file)


if __name__ == '__main__':
    gc = SweatybettyOutput()
    gc.output_to_excel()
