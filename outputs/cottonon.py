from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput
import json


class CottononOutput(BaseOutput):

    site_name = 'cottonon'

    def __init__(self):
        super(CottononOutput, self).__init__('商品信息列表', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'CODE', 'SPU', '图片', '分类', '商品标题', '商品链接', '更新时间', '评论数', '价格/AU$', '颜色数',
                     '推荐', '不推荐', '面料', '商品特性')
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
            details = json.loads(goods.details)
            features_text = ""
            for feature in details["features_list"]:
                features_text += feature + "\n"
            recommended_count = 0
            not_recommended_count = 0
            for item in details["recommended_distribution_list"]:
                if item["key"]:
                    recommended_count = item["count"]
                else:
                    not_recommended_count = item["count"]

            goods_info_list = [
                goods.id, goods.code, goods.asin, image, goods.category_name, goods.title, goods.url, time_str,
                goods.reviews_num, goods.price, details["color_num"], recommended_count, not_recommended_count,
                details["composition"], features_text
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = CottononOutput()
    ot.output()
