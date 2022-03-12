import json

from pyscrapy.models import Goods, GoodsCategory, Translator as TranslatorModel
from outputs.baseoutput import BaseOutput
import time
# from translate import Translator


class SweatybettyOutput(BaseOutput):

    site_name = 'sweatybetty'
    # translator: Translator
    categories: list

    # trans_dic = {}

    def __init__(self):
        super(SweatybettyOutput, self).__init__('商品信息', self.site_name)
        self.categories = self.db_session.query(GoodsCategory).all()
        # self.translator = Translator(to_lang='chinese', provider='mymemory')  # , proxies={'http': '127.0.0.1:1080'}
        # all_trans = self.db_session.query(TranslatorModel).all()
        # for trans in all_trans:
        #     self.trans_dic[trans.from_lang] = trans.to_lang

    # def to_chinese(self, content: str):
    #     return self.translator.translate(content)

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
                    fabric = details['fabric']
                    fabric_list = []
                    fa1_list = fabric.split(',')
                    for fa1 in fa1_list:
                        fa2_list = fa1.split('%')
                        try:
                            fabric_ele = fa2_list[1].strip()
                        except IndexError:
                            fabric_ele = fa2_list[0].strip()
                            print(fabric_ele)
                            print(str(goods.id))

                        # if fabric_ele not in self.trans_dic:
                            # to_lang = self.to_chinese(fabric_ele)
                            # print(to_lang)
                            # if to_lang.find('MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR') >= 0:
                            #     to_lang = fabric_ele
                            # to_lang = fabric_ele
                            # self.trans_dic[fabric_ele] = to_lang
                            # trans_model = TranslatorModel(from_lang=fabric_ele, to_lang=to_lang)
                            # self.db_session.add(trans_model)
                            # self.db_session.commit()
                        fabric_list.append(fabric_ele)
                    for fabric_item in fabric_list:
                        fabric += fabric_item
                    #     fabric = fabric.replace(fabric_item, self.trans_dic[fabric_item])

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
