from utils.pyfile import get_attr_to_cls


def export_spider_data(spider_name: str):
    print("-----exporting data from spider: " + spider_name)
    spidercls = get_attr_to_cls('name', 'pyscrapy.spiders').get(spider_name)
    fields = getattr(spidercls, 'custom_settings').get('FEED_EXPORT_FIELDS')
    exportfunc = getattr(spidercls, 'export', None)
    if exportfunc is None:
        print("No export function found in spider({}). use common function to export. FEED_EXPORT_FIELDS is ({})".format(spider_name, fields))
        return
    exportfunc()

def to_str(v):
    if isinstance(v, list):
        return ",".join(v)
    return ""

def get_field_value_to_excel(k: str, v):
    if k == 'Tags' or k == 'SizeList':
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

