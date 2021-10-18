from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from Config import Config
from service.DB import DB
from pyscrapy.models import Site
import os
import time
from sqlalchemy.orm.session import Session


class BaseOutput:

    site_name: str
    site_id: int
    db_session: Session
    wb: Workbook
    work_sheet: Worksheet
    output_dir = Config.ROOT_PATH + '/runtime'
    output_file = output_dir + '/output' + time.strftime("%Y-%m-%d_%H_%M", time.localtime()) + '.xlsx'

    def __init__(self, sheet_title='库存详情'):
        db = DB(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
        # TODO 因文件名故，xlsx文件通常仅走新增路线
        if os.path.isfile(self.output_file):
            self.wb = load_workbook(self.output_file)
            self.work_sheet = self.wb.worksheets[0]
        else:
            self.wb = Workbook()
            self.work_sheet = self.wb.create_sheet(index=0, title=sheet_title)
        site = self.db_session.query(Site).filter(Site.name == self.site_name).first()
        if not site:
            raise RuntimeError(self.site_name + " 在数据库中不存在")
        self.site_id = site.id

    @staticmethod
    def set_values_to_row(sheet: Worksheet, values_list: tuple, row_index, start_col=1):
        for cell_value in values_list:
            sheet.cell(row_index, start_col, cell_value)
            start_col += 1
        return start_col

    @staticmethod
    def timestamp_to_str(timestamp=None, format_str="%Y-%m-%d %H:%M") -> str:
        time_tuple = time.localtime(timestamp)
        return time.strftime(format_str, time_tuple)

    # def output_to_excel(self):
        # sheet = self.work_sheet
        # # sheet.sheet_format.defaultRowHeight = 30
        # title_row = ('商品ID', '分类名', '商品名', '商品链接', '商品状态', '更新时间', '规格1', '规格2', 'SKU名', '价格', '库存')
        # title_col = 1
        # for title in title_row:
        #     sheet.cell(1, title_col, title)
        #     title_col += 1
        # goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        # sku_row_index = 2
        #
        # for goods in goods_list:
        #     goods_col_index = 1
        #     start_row_index = sku_row_index
        #     time_str = self.timestamp_to_str(goods.updated_at)
        #     # 商品信息元组
        #     goods_info_list = (goods.id, goods.category_name, goods.title, goods.url, Goods.statuses_map[goods.status], time_str)
        #     # 返回商品信息递增列 next col index
        #     goods_col_index = self.set_values_to_row(sheet, goods_info_list, sku_row_index, goods_col_index)

        # self.wb.save(self.output_file)


if __name__ == '__main__':
    output = BaseOutput()
    # output.output_to_excel()
