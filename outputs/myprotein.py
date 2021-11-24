from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput
from pyscrapy.spiders.amazon import AmazonSpider
import json


class MyproteinOutput(BaseOutput):
    site_name = 'myprotein'

    def __init__(self):
        super(MyproteinOutput, self).__init__('商品信息列表', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'code', '图片', '分类', '商品标题', '商品链接', '更新时间', '价格/£', '评论数', '状态',
                     '品牌', '评分', '应用范围', '商品概述', '商品特性')
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
            image = ''
            if goods.local_image:
                image = self.get_image_info(goods.local_image)
            details = json.loads(goods.details)
            brand = details['brand']
            rating_value = details['rating_value']
            goods_range = details['range'] if 'range' in details else ''
            overview = ''
            if 'overview' in details:
                for oview in details['overview']:
                    overview += oview + '\n'
            benefits = ''
            if 'benefits' in details:
                for benefit in details['benefits']:
                    benefits += benefit + "\n"
            goods_url = goods.url

            goods_info_list = [
                goods.id, goods.code, image, goods.category_name, goods.title, goods_url, time_str, goods.price,
                goods.reviews_num, Goods.statuses_map[goods.status], brand, rating_value,
                goods_range, overview, benefits
            ]
            print('================')
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = MyproteinOutput()
    ot.output()
