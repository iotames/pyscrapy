from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput
import json


class SheinOutput(BaseOutput):
    site_name = 'shein'

    def __init__(self):
        super(SheinOutput, self).__init__('商品明细', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('ID', '图片', '排名', '上架时间（首个评论）', 'goods_id', 'SPU', '颜色', '品类', '商品标题', '商品链接', '更新时间',
                     '价格/US$', '评论数', '销量(评论*20)', '销售额(估算)', '所属品牌', 'SKU数', '1星评论数')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
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

            brand = details['brand']
            spu = details['spu']
            goods_id = details['goods_id']
            color = details['color']
            total_rank1 = details['total_rank1'] if 'total_rank1' in details else 0
            relation_colors = details['relation_colors']
            sku_num = 1
            if relation_colors:
                sku_num += len(relation_colors)
            category_name = goods.category_name
            goods_url = goods.url
            reviews_num = goods.reviews_num

            goods_info_list = [
                goods.id, image, details['rank_in'], first_at, goods_id, spu, color, category_name, goods.title, goods_url, updated_at,
                goods.price, reviews_num, reviews_num*20, reviews_num*20*goods.price, brand, sku_num, total_rank1
            ]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = SheinOutput()
    ot.output()
