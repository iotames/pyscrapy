import getopt
import sys
import threading
import time
import webbrowser
from config.api_server import ApiServer
from config.client import Client
from api import app
from pyscrapy.helpers.Socket import Socket
# import asyncio

port = ApiServer().get_config().get('port')
url = Client().get_config().get('start_url')


# async def open_web_server():
def open_web_server():
    if Socket.check_port_used(port):
        print('Port: ' + str(port) + " is Exists")
    else:
        app.run(port=port)


# async def open_url(url):
#     await asyncio.sleep(3)
def open_url():
    time.sleep(1)
    webbrowser.open(url)


class myThread (threading.Thread):
    def __init__(self, thread_id, name, func):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.func = func

    def run(self):
        print("开始线程：" + self.name)
        self.func()

# async def main():
#     await asyncio.gather(
#         open_web_server(),
#         open_url(url)
#     )


if __name__ == '__main__':
    argvs = sys.argv
    t1 = myThread(1, 't1', open_web_server)
    t2 = myThread(2, 't2', open_url)
    if not argvs[1:]:
        t1.start()
        t2.start()
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
                t1.start()
            if opt in ('-c', '--start-client'):
                t2.start()
    # asyncio.run(main())
    # t1 = threading.Thread(target=open_web_server())
    # t2 = threading.Thread(target=open_url())

