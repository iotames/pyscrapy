# import getopt
# import sys
import time
import webbrowser
from config.api_server import ApiServer
from config.client import Client
from api import app
from pyscrapy.helpers.Socket import Socket
# from service import SThread
# import asyncio
# https://github.com/pyinstaller/pyinstaller/issues/4815
import scrapy.utils.misc
import scrapy.core.scraper


def warn_on_generator_with_return_value_stub(spider, callable):
    pass


scrapy.utils.misc.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub
scrapy.core.scraper.warn_on_generator_with_return_value = warn_on_generator_with_return_value_stub

port = ApiServer().get_config().get('port')
url = Client().get_config().get('start_url')


def open_web_server():
    if Socket.check_port_used(port):
        print('Port: ' + str(port) + " is Exists")
    else:
        app.run(port=port)


def open_url():
    time.sleep(1)
    webbrowser.open(url)


if __name__ == '__main__':
    open_web_server()
"""
    argvs = sys.argv
    sth = SThread.get_instance()
    if not argvs[1:]:
        sth.run_task(open_web_server)
        sth.run_task(open_url)
    else:
        help_str = "WebServer.py --start-server --start-client"
        try:
            opts, args = getopt.getopt(argvs[1:], "hsc", ["help", "start-server", 'start-client'])
        except getopt.GetoptError:
            print(help_str)
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", '--help'):
                print(help_str)
                sys.exit()
            if opt in ('-s', '--start-server'):
                sth.run_task(open_web_server)
            if opt in ('-c', '--start-client'):
                sth.run_task(open_url)
"""
    # asyncio.run(main())
    # t1 = threading.Thread(target=open_web_server())
    # t2 = threading.Thread(target=open_url())

