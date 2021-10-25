from pyscrapy.models import Goods
from outputs.baseoutput import BaseOutput


class StrongerlabelOutput(BaseOutput):

    site_name = 'strongerlabel'
    
    def __init__(self):
        super(StrongerlabelOutput, self).__init__('商品库存', self.site_name)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', '分类名', '商品名', '商品链接', '商品状态', '更新时间', '价格', '库存')
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
            goods_info_list = (goods.id, goods.category_name, goods.title, goods.url, Goods.statuses_map[goods.status], time_str, goods.price, goods.quantity)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    sl = StrongerlabelOutput()
    sl.output()
