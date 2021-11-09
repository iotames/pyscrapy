from flask import Flask
from config.api_server import ApiServer
from api.response import Response

app = Flask(
    __name__,
    static_folder=ApiServer().get_config().get('static_folder'),
    static_url_path='/'
)

from api import routes
