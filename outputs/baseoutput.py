from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from Config import Config
from service.DB import DB
from pyscrapy.models import Site
import os
import time
from sqlalchemy.orm.session import Session
from scrapy.utils.project import get_project_settings
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter


class BaseOutput:

    site_name: str
    site_id: int
    db_session: Session
    wb: Workbook
    work_sheet: Worksheet
    output_dir = Config.ROOT_PATH + '/runtime'
    output_file: str = output_dir + '/{}_' + time.strftime("%Y-%m-%d_%H_%M", time.localtime()) + '.xlsx'
    images_dir: str

    def __init__(self, sheet_title='库存详情', filename='output'):
        self.images_dir = get_project_settings().get('IMAGES_STORE')
        db = DB(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
        # TODO 因文件名故，xlsx文件通常仅走新增路线
        self.output_file = self.output_file.format(filename)
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

    def get_image_info(self, path: str) -> dict:
        image_path = self.images_dir + os.path.sep + path
        if not os.path.isfile(image_path):
            return {'type': str, 'path': image_path}
        image = {
            'type': Image,
            'path': image_path,
            'size': (100, 100)
        }
        return image

    @staticmethod
    def set_values_to_row(sheet: Worksheet, values_list: list, row_index, start_col=1):
        for cell_value in values_list:
            if isinstance(cell_value, dict):
                if cell_value['type'] == Image:
                    # print('===========================================Image===' + cell_value['path'])
                    image = Image(cell_value['path'])
                    image.width, image.height = cell_value['size']
                    image.anchor = get_column_letter(start_col) + str(row_index)
                    print(image.anchor)
                    sheet.add_image(image)
                if cell_value['type'] == str:
                    sheet.cell(row_index, start_col, cell_value['path'])
            else:
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
