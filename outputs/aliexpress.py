from pyscrapy.models import Goods, SpiderRunLog, GroupLog, GroupGoods
from outputs.baseoutput import BaseOutput
import json
from pyscrapy.enum.spider import *
from time import time


class AliexpressOutput(BaseOutput):

    site_name = NAME_ALIEXPRESS

    def __init__(self, run_log: SpiderRunLog):
        self.child = run_log.spider_child
        link_id = run_log.link_id
        query_args = {"id": int(link_id)}

        self.group_log_model = GroupLog.get_model(GroupGoods.get_db_session(), query_args)
        self.group_name = self.group_log_model.code

        filename = "{}_{}".format(self.site_name, self.group_name).replace(' ', '_').replace("'", "-").replace("&",
                                                                                                               "and")
        self.download_filename = "{}_{}.xlsx".format(filename, link_id)
        super(AliexpressOutput, self).__init__('商品信息列表', filename)

    @property
    def log_model(self):
        return self.group_log_model

    def output(self):
        sheet = self.work_sheet

        if not self.log_model:
            raise RuntimeError('找不到排行榜数据')
        if time() - self.log_model.created_at > 3600 * 72:
            raise RuntimeError('最近排行榜数据已超过72小时, 请重新采集')

        x_goods_list = self.db_session.query(GroupGoods).filter_by(**{'group_log_id': self.log_model.id}).order_by(
            GroupGoods.rank_num.asc()).all()

        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'SPU', '图片', '分类', '商品标题', '商品链接', '更新时间', '价格',
                     '销量', '评分', '店铺', '店铺链接')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_row_index = 2

        for x_goods in x_goods_list:
            goods_col_index = 1
            goods_model = Goods.get_model(self.db_session, {'id': x_goods.goods_id})
            time_str = self.timestamp_to_str(goods_model.updated_at, "%Y-%m-%d %H:%M")
            # 商品信息元组
            image = self.get_image_info(goods_model.local_image) if goods_model.local_image else ''
            if not goods_model.details:
                print(goods_model.id)
                raise ValueError("goods_model details can not be None")
            details = json.loads(goods_model.details)
            store_name = details['store_name']
            store_url = details['store_url']
            rating_value = details['rating_value']
            sales_num = goods_model.sales_num
            goods_url = goods_model.url
            category_name = goods_model.category_name if goods_model.category_name else self.log_model.code

            goods_info_list = [
                goods_model.id, goods_model.asin, image, category_name, goods_model.title, goods_url, time_str, goods_model.price_text,
                sales_num, rating_value, store_name, store_url
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1
        self.wb.save(self.output_file)


if __name__ == '__main__':

    db_session = SpiderRunLog.get_db_session()
    log = SpiderRunLog.get_model(db_session, {'id': 3})
    ot = AliexpressOutput(log)
    ot.output()
