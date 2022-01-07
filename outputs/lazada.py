from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput
import json
from pyscrapy.enum.spider import *


class LazadaOutput(BaseOutput):

    site_name = NAME_LAZADA

    def __init__(self):
        super(LazadaOutput, self).__init__('商品信息列表', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'SPU', '图片', '商品标题', '商品链接', '更新时间', '价格', '价格', '原价', '折扣',
                     '评论数', '评分', '品牌', '地区',)
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
                exit()
            details = json.loads(goods.details)
            brand = details['brand']
            original_price = details['original_price'] if 'original_price' in details else ''
            discount = details['discount'] if 'discount' in details else ''
            location = details['location'] if 'location' in details else ''
            rating_score = details['rating_score'] if 'rating_score' in details else ''
            goods_url = goods.url

            goods_info_list = [
                goods.id, goods.asin, image, goods.title, goods_url, time_str, goods.price_text, goods.price,
                original_price, discount, goods.reviews_num, rating_score, brand, location
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = LazadaOutput()
    ot.output()
