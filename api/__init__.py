from flask import Flask
from flask_cors import CORS
from config.api_server import ApiServer
from api.response import Response
from Config import Config

# 兼容相对路径写法。 否则配置文件使用相对路径无效。
static_folder = Config.get_abspath(ApiServer().get_config().get('static_folder'))
app = Flask(
    __name__,
    static_folder=static_folder,
    static_url_path='/'
)
# https://blog.csdn.net/joker_zsl/article/details/116452374  flask踩坑记录：flask的响应结果总是按首字母排序
# app.config['JSON_SORT_KEYS'] = False

CORS(app, supports_credentials=True)
from api import routes
