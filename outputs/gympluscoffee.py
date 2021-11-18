import json

from pyscrapy.models import Goods, GoodsSku, GoodsCategory
from outputs.baseoutput import BaseOutput
import time
from translate import Translator
from openpyxl import load_workbook


class GympluscoffeeOutput(BaseOutput):

    site_name = 'gympluscoffee'
    translator: Translator
    categories: list
    goods_model_list: list

    def __init__(self):
        super(GympluscoffeeOutput, self).__init__('SKU库存详情', self.site_name)
        self.categories = self.db_session.query(GoodsCategory).all()
        self.translator = Translator(to_lang='chinese', provider='mymemory')

    def to_chinese(self, content: str):
        return self.translator.translate(content)

    def get_parent_by_category_id(self, category_id: int):
        parent_id = 0
        model = None
        for category in self.categories:
            if category.id == category_id:
                parent_id = category.parent_id
                break
        for category in self.categories:
            if category.id == parent_id:
                model = category
        return model

    def output_to_excel(self):
        sheet = self.work_sheet
        sheet.sheet_format.defaultRowHeight = 100
        # sheet.sheet_format.defaultColWidth = 100
        title_row = ('商品ID', '图片', '上级分类', '分类名', '商品标题', '商品链接', '商品状态', '更新时间',
                     '评论数', '价格/EUR', '商品简介', '商品详情', '织物布料',
                     '5星评论', '4星评论', '3星评论', '2星评论', '1星评论',
                     '规格1', '规格2', 'SKU名', '价格', '库存')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        self.goods_model_list = self.db_session.query(Goods).filter(Goods.site_id == self.site_id).all()

        goods_urls = []
        for model in self.goods_model_list:
            if model.url in goods_urls:
                # 剔除可能重复的商品项
                self.goods_model_list.remove(model)
            else:
                goods_urls.append(model.url)

        sku_row_index = 2

        for goods in self.goods_model_list:
            goods_col_index = 1
            start_row_index = sku_row_index
            time_tuple = time.localtime(goods.updated_at)
            time_str = time.strftime("%Y-%m-%d %H:%M", time_tuple)
            reviews_num = goods.reviews_num
            details = goods.details
            price = goods.price
            schema = ''
            detail = ''
            fabric = ''
            rating5, rating4, rating3, rating2, rating1 = (0, 0, 0, 0, 0)
            if details:
                details = json.loads(details)
                schema = details['schema']  # + " 翻译： " + self.to_chinese(details['schema'])
                detail = details['details']  # + " 翻译： " + self.to_chinese(details['details'])
                fabric = details['fabric']  # + " 翻译： " + self.to_chinese(details['fabric'])
                if reviews_num > 0:
                    rating = details['rating']
                    rating5 = rating['5']
                    rating4 = rating['4']
                    rating3 = rating['3']
                    rating2 = rating['2']
                    rating1 = rating['1']
            # 商品信息元组
            image = ''
            if goods.local_image:
                image = self.get_image_info(goods.local_image)
            p_category_name = ''
            p_category = self.get_parent_by_category_id(goods.category_id)
            if p_category:
                p_category_name = p_category.name
            goods_info_list = [goods.id, p_category_name, goods.category_name, goods.title, goods.url,
                               Goods.statuses_map[goods.status], time_str,
                               reviews_num, price, schema, detail, fabric, rating5, rating4, rating3, rating2, rating1]
            goods_row_info = goods_info_list.copy()
            goods_row_info.insert(1, image)
            # print(goods_row_info)
            # 返回商品信息递增列 next col index
            goods_col_index = self.set_values_to_row(sheet, goods_row_info, sku_row_index, goods_col_index)

            goods_sku_list = self.db_session.query(GoodsSku).filter(
                GoodsSku.site_id == self.site_id, GoodsSku.goods_id == goods.id).all()
            sku_len = len(goods_sku_list)
            for sku in goods_sku_list:
                if sku_row_index > start_row_index:
                    # goods的SKU数量大于1， 从当前EXCEL行数量另起一行，复制goods基本信息填入。
                    goods_col_index = 1
                    if sku.local_image:
                        image = self.get_image_info(sku.local_image)
                    # 从第2个SKU开始，从goods拷贝基本信息
                    sku_row_info = goods_info_list.copy()
                    sku_row_info.insert(1, image)
                    print(sku_row_info)
                    # 从第2个SKU开始，都要拷贝goods基本信息写入EXCEL
                    goods_col_index = self.set_values_to_row(sheet, sku_row_info, sku_row_index, goods_col_index)
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

    # 重置EXCEL表格中URL和SKU重复的条目库存
    def update_excel(self, filepath):
        self.wb = load_workbook(filepath)
        self.work_sheet = self.wb.worksheets[0]
        print(self.work_sheet.rows)
        print(self.work_sheet[3][5].value)

        row_index = 1
        url_sku_list = []
        del_rows_index_list = []
        del_rows_list = []
        for row_data in self.work_sheet:
            url = row_data[5].value
            if not url:
                continue
            sku_text = row_data[20].value
            if not sku_text:
                continue

            url_sku = url + sku_text
            if url_sku in url_sku_list:
                row_data[22].value = "---"
                row_data[23].value = "---"
                row_data[24].value = "---"
                row_data[25].value = "---"
                del_rows_index_list.append(row_index)
                del_rows_list.append(url_sku)
            else:
                url_sku_list.append(url_sku)
            row_index += 1
        print(del_rows_index_list)
        print(del_rows_list)
        # for rowi in del_rows_index_list:
        #     url = self.work_sheet[rowi][5].value
        #     sku_text = self.work_sheet[rowi][20].value
        #     print('================begin==============')
        #     if not sku_text:
        #         continue
        #     print(rowi)
        #     print(str(rowi) + "--" + url + "  " + sku_text)
        #     # self.work_sheet.cell(rowi, 2, '')
        #     # self.work_sheet.
        #     self.work_sheet.delete_rows(rowi)  # delete_rows(1) 表示删除表格的第一行
        self.wb.save(self.output_file)


if __name__ == '__main__':
    gc = GympluscoffeeOutput()
    gc.update_excel(gc.output_dir + "/gympluscoffee_2021-11-16_16_56.xlsx")
    # gc.output_to_excel()
