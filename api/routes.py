from api import app, Response
from api.SpiderController import SpiderController
from flask import request
# import json


# @app.route('/api/page/schema')
# def page_schema():
#     component = request.args.get('component')
#     name = request.args.get('name')
#     return Response.data(PageSchema.get_data(component, name))
#
# @app.route('/vue-element-admin/user/login', methods=['POST'])
# def login():
#     return Response.data({"token": "admin-token"})

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
