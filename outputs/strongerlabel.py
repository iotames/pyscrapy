from pyscrapy.models import Goods, GoodsQuantityLog, SpiderRunLog
from outputs.baseoutput import BaseOutput
from datetime import datetime
from pyscrapy.enum.spider import *
# from sqlalchemy import and_, or_


class StrongerlabelOutput(BaseOutput):

    site_name = NAME_STRONGERLABEL

    quantity_map = {}
    run_log: SpiderRunLog
    
    def __init__(self, run_log: SpiderRunLog):
        self.run_log = run_log
        # TODO BUG GoodsQuantityLog 商品不完整
        quantity_logs = GoodsQuantityLog.get_all_model(GoodsQuantityLog.get_db_session(), {'log_id': run_log.id})
        for quantity_log in quantity_logs:
            self.quantity_map[str(quantity_log.goods_id)] = quantity_log.quantity
        filename = "{}_".format(self.site_name).replace(' ', '_').replace("'", "-").replace("&", "and")
        self.download_filename = "{}_{}.xlsx".format(filename, str(run_log.id))
        super(StrongerlabelOutput, self).__init__('商品库存', filename)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        dtime: datetime = self.run_log.datetime
        title_row = ('商品ID', 'CODE', '图片', '分类名', '商品名', '商品链接', '商品状态', '更新时间', '价格', '库存' + dtime.strftime("%Y_%m_%d"))
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
            log_quantity = self.quantity_map[str(goods.id)] if str(goods.id) in self.quantity_map else 0
            goods_info_list = [goods.id, goods.code, image, goods.category_name, goods.title, goods.url, status_text,
                               time_str, goods.price, log_quantity]
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)
        self.copy_to_download_path(self.output_file)


if __name__ == '__main__':
    db_session = SpiderRunLog.get_db_session()
    log = SpiderRunLog.get_model(db_session, {'id': 193})
    sl = StrongerlabelOutput(log)
    sl.output()
