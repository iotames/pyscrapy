from openpyxl import Workbook
from Config import Config
from service.DB import DB
from pyscrapy.models import Goods, GoodsSku


class GympluscoffeeSpider:

    site_id = 1
    db_session = None
    excel: Workbook
    output_dir = Config.ROOT_PATH + '/runtime'

    def __init__(self):
        db = DB(Config().get_database())
        db.ROOT_PATH = Config.ROOT_PATH
        self.db_session = db.get_db_session()
        self.excel = Workbook()

    def output_to_excel(self):
        sheet = self.excel.active
        # sheet.sheet_format.defaultRowHeight = 30
        sheet.append(('ID', '尺寸', '颜色', 'SKU名', '价格', '库存'))
        # , '状态', '更新时间'
        # goods_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()
        # for goods in goods_list:
        goods_sku_list = self.db_session.query(GoodsSku).filter(GoodsSku.site_id == self.site_id).all()
        for sku in goods_sku_list:
            row = (sku.id, sku.option1, sku.option2, sku.title, sku.price/100, sku.inventory_quantity)
            sheet.append(row)
        self.excel.save(self.output_dir + '/GympluscoffeeSpider.xlsx')


if __name__ == '__main__':
    gc = GympluscoffeeSpider()
    gc.output_to_excel()
