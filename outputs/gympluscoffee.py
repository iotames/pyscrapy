from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from Config import Config
from service.DB import DB
from pyscrapy.models import Goods, GoodsSku
import os
import time


class GympluscoffeeSpider:

    site_id = 1
    db_session = None
    wb: Workbook
    work_sheet: Worksheet
    output_dir = Config.ROOT_PATH + '/runtime'
    output_file = output_dir + '/GympluscoffeeSpider' + time.strftime("%Y-%m-%d_%H_%M", time.localtime()) + '.xlsx'

    def __init__(self):
        db = DB(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
        # TODO 因文件名故，xlsx文件通常仅走新增路线
        if os.path.isfile(self.output_file):
            self.wb = load_workbook(self.output_file)
            self.work_sheet = self.wb.worksheets[0]
        else:
            self.wb = Workbook()
            self.work_sheet = self.wb.create_sheet(index=0, title='SKU库存详情')

    @staticmethod
    def set_values_to_row(sheet: Worksheet, values_list: tuple, row_index, start_col=1):
        for cell_value in values_list:
            sheet.cell(row_index, start_col, cell_value)
            start_col += 1
        return start_col

    def output_to_excel(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', '分类名', '商品名', '商品链接', '商品状态', '更新时间', '规格1', '规格2', 'SKU名', '价格', '库存')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        sku_row_index = 2

        for goods in goods_list:
            goods_col_index = 1
            start_row_index = sku_row_index
            time_tuple = time.localtime(goods.updated_at)
            time_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
            # 商品信息元组
            goods_info_list = (goods.id, goods.category_name, goods.title, goods.url, Goods.statuses_map[goods.status], time_str)
            # 返回商品信息递增列 next col index
            goods_col_index = self.set_values_to_row(sheet, goods_info_list, sku_row_index, goods_col_index)

            goods_sku_list = self.db_session.query(GoodsSku).filter(
                GoodsSku.site_id == self.site_id, GoodsSku.goods_id == goods.id).all()
            sku_len = len(goods_sku_list)
            for sku in goods_sku_list:
                if sku_row_index > start_row_index:
                    goods_col_index = 1
                    goods_col_index = self.set_values_to_row(sheet, goods_info_list, sku_row_index, goods_col_index)
                price = format(sku.price/100, '.2f')
                sku_info_list = (sku.option1, sku.option2, sku.title, price, sku.inventory_quantity)
                # SKU信息列紧接商品信息列之后
                sku_col_index = goods_col_index
                for sku_info in sku_info_list:
                    sheet.cell(sku_row_index, sku_col_index, sku_info)
                    # SKU信息列递增
                    sku_col_index += 1
                sku_row_index += 1

            # if sku_len > 1:
            #     # 合并单元格
            #     start_row = start_row_index
            #     end_row = sku_row_index-1
            #     sheet.merge_cells('A{}:A{}'.format(start_row, end_row))
            #     sheet.merge_cells('B{}:B{}'.format(start_row, end_row))
            #     sheet.merge_cells('C{}:C{}'.format(start_row, end_row))
            #     sheet.merge_cells('D{}:D{}'.format(start_row, end_row))
            #     sheet.merge_cells('E{}:E{}'.format(start_row, end_row))
            #     sheet.merge_cells('F{}:F{}'.format(start_row, end_row))
            if sku_len == 0:
                sku_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':
    gc = GympluscoffeeSpider()
    gc.output_to_excel()
