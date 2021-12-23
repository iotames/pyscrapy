from api import app, Response
from api.SpiderController import SpiderController
from flask import request, redirect
from Config import Config
import os
# https://medium.com/analytics-vidhya/integrating-scrapy-with-flask-8611debc4579
import crochet
crochet.setup()


@app.route('/user/logout', methods=['POST', 'GET'])
def logout():
    return Response.success({})


@app.route('/api/spiders')
def get_spiders():
    items = SpiderController().get_spiders_list()
    return Response.success({"items": items})


@app.route('/api/spider/logs')
def get_spider_logs():
    name = request.args.get("name")
    items = SpiderController().get_spiders_run_logs(name)
    return Response.success({"items": items})


@app.route('/api/spider/log/excel', methods=['POST'])
def spider_log_excel():
    try:
        data = request.get_json()
        log_id = data.get('log_id')
        output = SpiderController().output_excel_by_run_log_id(log_id)
        url = request.url_root + output.downloads_dirname + "/" + output.download_filename
        if not output.is_download_file_exists():
            output.output()
    except Exception as e:
        return Response.error(str(e))
    return Response.success({'url': url, "filename": output.download_filename}, "操作成功: id={}".format(str(log_id)))


@app.route('/api/database/init', methods=['POST'])
def database_init():
    from service import DB
    from pyscrapy.models import Table
    config = Config()
    db = DB(config.get_database())
    db.ROOT_PATH = config.ROOT_PATH
    engine = db.get_db_engine()
    Table.create_all_tables(engine)
    return Response.success({})


@crochet.run_in_reactor
def run_spider(spider_name, child_name):
    from scrapy.utils.project import get_project_settings
    from scrapy.crawler import CrawlerRunner
    crawl_runner = CrawlerRunner(get_project_settings())

    dirpath = Config.get_logs_dir()
    spider_args = {
        'logs_dir': dirpath,
        'spider_child': child_name,
        'log_id': "",  # "39"
    }
    print('======spider args = ')
    print(spider_args)
    # from scrapy.crawler import CrawlerProcess
    # process = CrawlerProcess(get_project_settings())
    # process.crawl(spider_name, **spider_args)
    # process.start()
    crawl_runner.crawl(spider_name, **spider_args)


@app.route('/api/task/create', methods=['POST'])
def create_spider_task():
    data: dict = request.get_json()
    spider_name = data.get('name')
    child_name = data.get('child_name')
    print(data)
    run_spider(spider_name, child_name)
    return Response.success({}, '爬虫任务创建成功')


@app.route('/api/table/columns')
def get_table_columns():
    name = request.args.get("name")
    return Response.success({"items": SpiderController.get_table_columns(name)})


@app.route('/api/config/<item>', methods=['POST'])
def update_config(item):
    # post_data = json.loads(request.get_data())
    from config.baseconfig import BaseConfig
    import json
    filepath = BaseConfig.CONFIG_DIR_PATH + os.sep + item + ".json"
    if not os.path.isfile(filepath):
        return Response.error('{} : 文件不存在'.format(filepath), 500)

    post_data = request.get_json()
    print(item)
    print(post_data)

    file_stream = open(filepath, '+', encoding='utf-8')
    data: dict = json.load(file_stream)
    print(data)
    # 更新原配置
    data.update(post_data)
    print(data)
    # 写入原配置
    json.dump(data, file_stream, ensure_ascii=False)
    file_stream.close()
    return Response.data({}, '提交成功')


@app.errorhandler(404)
def page_redirect(error):
    print('====================404=========')
    print(request.path)
    print(error)
    # return Response.success({"hello": "word"})
    return redirect('/index.html?page=' + request.path)
