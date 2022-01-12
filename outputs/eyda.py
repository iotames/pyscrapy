from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput
import json


class EydaOutput(BaseOutput):

    site_name = 'eyda'

    def __init__(self):
        super(EydaOutput, self).__init__('商品信息列表', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'SPU', '图片', '分类', '商品标题', '商品链接', '更新时间', '价格/€', '状态',
                     '库存', '颜色款数', '面料')
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
            if not goods.details:
                print(goods.id)
                raise ValueError("goods details can not be None")
            details = json.loads(goods.details)

            colors = details['colors_list']  # if 'colors' in details else []
            colors_len = len(colors)
            composition_text = details['composition_text']
            goods_url = goods.url

            goods_info_list = [
                goods.id, goods.asin, image, goods.category_name, goods.title, goods_url, time_str, goods.price,
                Goods.statuses_map[goods.status], goods.quantity, colors_len, composition_text
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = EydaOutput()
    ot.output()
