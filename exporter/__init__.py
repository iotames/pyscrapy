from utils.pyfile import get_attr_to_cls
from service.Exporter import Exporter


def export_spider_data(spider_name: str):
    print("-----exporting data from spider: " + spider_name)
    spidercls = get_attr_to_cls('name', 'pyscrapy.spiders').get(spider_name)
    fields = getattr(spidercls, 'custom_settings').get('FEED_EXPORT_FIELDS')
    get_export_data = getattr(spidercls, 'get_export_data', None)
    data_list = []
    if get_export_data is None:
        print("No get_export_data function found in spider({}). use common function to export. FEED_EXPORT_FIELDS is ({})".format(spider_name, fields))
        # TODO
    else:
        data_list = get_export_data()
    if len(data_list) == 0:
        raise Exception("No data to export")
    exp = Exporter(spider_name)
    exp.append_row(fields)
    for row_data in data_list:
        exp.append_row(row_data)
    # imgs = [exp.get_image_by_filename("0a5890653dd80b014a9a010deecd7ba2.jpg", "4tharq")]
    # id = 2
    # for img in imgs:
    #     exp.add_image(img, 1, id)
    #     id += 1
    exp.save()


def to_str(v):
    if isinstance(v, list):
        return ",".join(v)
    return ""

def get_field_value_to_excel(k: str, v):
    if k == 'Tags' or k == 'SizeList' or k == 'Gender':
        return to_str(v)
    if k == 'OldPrice' or k == 'FinalPrice':
        return float(v)
    if k == 'Thumbnail':
        if v and v.startswith("//"):
            return "https:" + v
    return v

def get_row_data(fields: list, item) -> list:
    row = []
    for k in fields:
        cellvalue = ""
        v = item.get(k, None)
        if v is not None:
            cellvalue = get_field_value_to_excel(k, v)
        # if k in item:
        #     v = item[k]
        #     if v is not None:
        #         cellvalue = get_field_value_to_excel(k, v)
        row.append(cellvalue)
    return row

