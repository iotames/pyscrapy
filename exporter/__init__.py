from utils.pyfile import get_attr_to_cls
from service.Exporter import Exporter
from service import Config
from models import UrlRequest
from datetime import datetime, timedelta
from sqlalchemy import and_
import os
import requests
import shutil


def get_spider_data(site_id: int, step: int) ->list:
    data_list = []
    select_fields = [UrlRequest.data_format, UrlRequest.collected_at]
    print("site_id:", site_id)
    reqs = UrlRequest.query(select_fields).filter(and_(
        UrlRequest.site_id == site_id,
        UrlRequest.updated_at > (datetime.now() - timedelta(hours=23)),
        UrlRequest.step == step
        )).all()
    if step == 0:
        for req in reqs:
            data_list.append(req.data_format)
    if step == 1:
        for req in reqs:
            dl = req.data_format.get('ProductList', None)
            if dl is None:
                raise Exception("ProductList could not be None")
            for dd in dl:
                data_list.append(dd)
    return data_list

def export_spider_data(spider_name: str, image_enable: bool):
    print("-----exporting data from spider: " + spider_name)
    spidercls = get_attr_to_cls('name', 'pyscrapy.spiders').get(spider_name)
    fields = getattr(spidercls, 'custom_settings').get('FEED_EXPORT_FIELDS')
    referer = getattr(spidercls, 'base_url', None)
    if referer is not None:
        referer = referer + "/"
    http_proxy = Config.get_instance().get_http_proxy()
    get_export_data = getattr(spidercls, 'get_export_data', None)
    data_list = []
    if get_export_data is None:
        # print("No get_export_data function found in spider({}). use common function to export. FEED_EXPORT_FIELDS is ({})".format(spider_name, fields))
        step = 1
        if hasattr(spidercls, 'parse_detail'):
            step = 0
        data_list = get_spider_data(spidercls.get_site_id(), step)
    else:
        data_list = get_export_data()
    # 导出数据为空时，抛出异常。避免生成空文件。
    if len(data_list) == 0:
        raise Exception("No data to export")
    # 准备导出数据
    exp = Exporter(spider_name)
    exp.append_row(fields)
    rowi = 2
    for dt in data_list:
        row_data = []
        if isinstance(dt, list):
            row_data = dt
        if isinstance(dt, dict):
            row_data = get_row_data(fields, dt)
        if len(row_data) != len(fields):
            raise Exception("Data length is not equal to fields length")
        imgurl = row_data[0]
        if imgurl is not None or imgurl != "":
            imgfilepath = exp.get_image_filepath_by_url(imgurl, spider_name)
            if not os.path.isfile(imgfilepath) and image_enable:
                # 如果图片文件不存在，下载并保存图片
                if download_image(imgurl, imgfilepath, referer, http_proxy):
                    print(f"Success: Image downloaded and saved to {imgfilepath}")
                else:
                    print(f"Failed: to download image from {imgurl}")
            if os.path.isfile(imgfilepath):
                row_data[0] = ""
                exp.add_image(exp.get_image_by_url(imgurl, spider_name), 1, rowi)
        exp.append_row(row_data)
        rowi += 1
    exp.save()

def to_str(v):
    if isinstance(v, list):
        vvv = []
        for vv in v:
            if vv is None:
                vvv.append("null")
            else:
                vvv.append(str(vv).strip())
        return ",".join(vvv)
        # return ",".join(v)
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

def download_image(url, filepath, referer=None, http_proxy=None):
    """下载图片并保存到指定路径，支持 referer 和 proxy 参数"""
    try:
        # 设置请求头，添加 referer
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        if referer is not None and referer != "":
            headers['Referer'] = referer

        # 设置代理
        proxies = {}
        if http_proxy is not None and http_proxy != "":
            proxies['http'] = http_proxy
            proxies['https'] = http_proxy
        print("----download_image--url({})--http_proxy({})--headers({})--".format(url, http_proxy, headers))
        # 发送请求下载图片
        response = requests.get(url, headers=headers, proxies=proxies, stream=True)
        if response.status_code == 200:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # 保存图片
            with open(filepath, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            return True
        else:
            print(f"Failed to download image from {url}. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return False
