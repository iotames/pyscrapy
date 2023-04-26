import json

from pyscrapy.models import SpiderRunLog
from outputs.strongerlabel import StrongerlabelOutput
from pyscrapy.enum.spider import *
from pyscrapy.models import Goods
from datetime import datetime


class AimnOutput(StrongerlabelOutput):

    site_name = NAME_AIMN

    def __init__(self, run_log: SpiderRunLog):
        super(AimnOutput, self).__init__(run_log)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        dtime: datetime = self.run_log.datetime
        title_row = ('商品ID', 'CODE', '图片', '分类名', '商品名', '商品链接', '商品状态', '更新时间', '价格', '吊牌价',
                     '库存' + dtime.strftime("%Y_%m_%d"), "详情")
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
            status_text = Goods.statuses_map[goods.status]
            details = json.loads(goods.details)
            desc = details["desc"] if "desc" in details else ""
            originalPriceText = details['origin_price_text']
            if originalPriceText == "":
                originalPriceText = "$"+str(goods.price)
            goods_info_list = [goods.id, goods.code, image, goods.category_name, goods.title, goods.url, status_text,
                               time_str, goods.price, originalPriceText, goods.quantity, desc]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            print(goods_row_index, goods.details)
            goods_row_index += 1
        self.wb.save(self.output_file)
        # self.copy_to_download_path(self.output_file)


if __name__ == '__main__':
    db_session = SpiderRunLog.get_db_session()
    log = SpiderRunLog.get_model(db_session, {'id': 50})
    sl = AimnOutput(log)
    sl.output()
