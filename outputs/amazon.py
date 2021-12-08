from pyscrapy.models import Goods, GoodsReview
from outputs.baseoutput import BaseOutput
from pyscrapy.spiders.amazon import AmazonSpider
import json
from sqlalchemy import and_
from openpyxl.styles import PatternFill


class AmazonOutput(BaseOutput):

    site_name = 'amazon'
    cell_fill = PatternFill("solid", fgColor="1874CD")
    goods_id_to_title = {}
    colors_show_times = {}
    
    def __init__(self):
        super(AmazonOutput, self).__init__('商品信息列表', self.site_name)

    def set_reviews_colors(self, reviews: list, detail_rows, color_partial=True):
        for review in reviews:
            product_title = self.goods_id_to_title[str(review.goods_id)]
            review_title = review.title
            rating = review.rating_value
            sku = review.sku_text
            url = review.url
            detail_rows.append((product_title, review_title, review.body, review.color, rating, sku, url, 0))
            if review.color is None:
                continue
            print(review.color)

            def set_colors_show_times(colorr: str):
                if colorr in self.colors_show_times:
                    self.colors_show_times[colorr] = self.colors_show_times[colorr] + 1
                else:
                    self.colors_show_times[colorr] = 1

            if color_partial:
                colors = review.color.split(' ')
                for color in colors:
                    set_colors_show_times(color)
            else:
                color = review.color
                set_colors_show_times(color)

    def output(self):
        sheet = self.work_sheet
        # sheet.sheet_format.defaultRowHeight = 30
        title_row = ('商品ID', 'code', '亚马逊ASIN', '分类', '图片', '商品标题', '商品链接', '上架时间', '更新时间', '价格/US$', '原价', '节省',
                     '评论数', '大类排名', '当前排名', '商品描述', '所有排名')
        title_col = 1
        for title in title_row:
            sheet.cell(1, title_col, title)
            title_col += 1
        goods_list = self.db_session.query(Goods).filter(
            Goods.site_id == self.site_id,
            # Goods.merchant_id == 1
        ).all()
        goods_row_index = 2

        for goods in goods_list:
            self.goods_id_to_title[str(goods.id)] = goods.title
            goods_col_index = 1
            time_str = self.timestamp_to_str(goods.updated_at, "%Y-%m-%d %H:%M")
            # 商品信息元组
            image = ''
            if goods.local_image:
                image = self.get_image_info(goods.local_image)
            details = json.loads(goods.details)

            sale_at = details['sale_at']
            asin = details['asin']
            root_rank = details['root_rank']
            goods_url = goods.url
            rank_list = details['rank_list']
            rank_num = details['rank_num'] if 'rank_num' in details else 0
            rank_detail = ''
            for rank in rank_list:
                # AmazonSpider.get_site_url(rank['url'])
                rank_detail += rank['category_text'] + " : " + rank['rank_text'] + '\n|'
            details_items = ""
            for item in details['items']:
                details_items += item + "\n|"
            goods_info_list = [
                goods.id, goods.code, asin, goods.category_name, image, goods.title, goods_url, sale_at, time_str, goods.price, details['price_base'],
                details['price_save'], goods.reviews_num, root_rank, rank_num, details_items, rank_detail
            ]
            print(goods_info_list)
            # 返回商品信息递增列 next col index
            self.set_values_to_row(sheet, goods_info_list, goods_row_index, goods_col_index)
            goods_row_index += 1

        # 标记重复的ASIN
        total_asin_list = []
        for row in sheet.rows:
            cell = row[2]
            asin = cell.value
            if asin in total_asin_list:
                cell.fill = self.cell_fill
                print(asin)
            else:
                total_asin_list.append(asin)

        sheet_reviews = self.wb.create_sheet(title='reviews', index=1)
        detail_rows = [('商品', '评论概要', '评论详情', '颜色', '评分', 'SKU', '评论源地址', '标记')]
        for goods in goods_list:
            reviews = self.db_session.query(GoodsReview).filter(
                and_(
                    GoodsReview.site_id == self.site_id,
                    GoodsReview.goods_id == goods.id
                )).all()
            self.set_reviews_colors(reviews, detail_rows, False)

        for row in detail_rows:
            sheet_reviews.append(row)
        for row in sheet_reviews.rows:
            for cell in row:
                if type(cell.value) == str:
                    if cell.value.find("size") > -1:
                        cell.fill = self.cell_fill
                        row[7].value = 1
                    if cell.value.find("Size") > -1:
                        cell.fill = self.cell_fill
                        row[7].value = 1

        self.wb.save(self.output_file)


if __name__ == '__main__':
    ot = AmazonOutput()
    ot.output()
