"""
@link https://www.selenium.dev/documentation/getting_started/installing_browser_drivers/#quick-reference

selenium 无法临时变更请求头， 无法获取响应头，如响应状态码
https://blog.csdn.net/weixin_29422697/article/details/112819239

@link https://cuiqingcai.com/8397.html 下载添加Selenium到下载中间件

"""
from selenium.webdriver import Chrome, Firefox, Ie, ChromeOptions, FirefoxOptions, IeOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from config.baseconfig import BaseConfig
from pyscrapy.helpers import Socket
import os


class Selenium(BaseConfig):

    name = 'selenium'

    DRIVER_CHROME = 'Chrome'
    DRIVER_FIREFOX = 'Firefox'
    DRIVER_EDGE = 'Edge'
    DRIVER_IE = 'Ie'

    DEFAULT_CONFIG = {
        "driver_browser": DRIVER_CHROME,
        "timeout": 30
    }

    SAMPLE_CONFIG = {
        "driver_browser": DRIVER_FIREFOX,
        "driver_path": "",
        "binary_location": "/opt/apps/org.mozilla.firefox-nal/files/firefox",  # /opt/google/chrome/google-chrome
        "debugger_address": "127.0.0.1:9222",
        "arguments": [
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--blink-settings=imagesEnabled=false",
            # INFO=0, WARNING=1, LOG_ERROR=2, LOG_FATAL=3
            # 禁用警告 "Error with Permissions-Policy header: Unrecognized feature: 'interest-cohort'."
            "--log-level=1",
            "--ignore-certificate-errors-spki-list",

            "--remote-debugging-port=9222",
            "--disable-popup-blocking",
            "--user-agent=\"Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0\"",
            # "--proxy-server=http://127.0.0.1:8083",
            "--user-data-dir=runtime/chrome_user_data"
        ],
        "window_size": {
            "width": 1920,
            "height": 1080
        }
    }

    def set_driver_params(self, params):
        config = self.config
        options = params['options']
        if 'driver_path' in config:
            # 浏览器驱动文件路径设置
            params['executable_path'] = config['driver_path']
        if 'debugger_address' in config:
            # 连接以远程端口调试模式启动的浏览器
            self.start_browser_by_remote_debugger()
            options.add_experimental_option('debuggerAddress', config['debugger_address'])
        else:
            if 'arguments' in config:
                # 非远程端口调试模式，可添加浏览器启动参数
                for arg in config['arguments']:
                    options.add_argument(arg)

    def get_chrome_driver(self):
        config = self.config
        options = ChromeOptions()
        if 'binary_location' in config:
            options.binary_location = config['binary_location']
        params = {'options': options}
        self.set_driver_params(params)
        return Chrome(**params)

    def get_firefox_driver(self):
        config = self.config
        options = FirefoxOptions()
        params = {'options': options}
        if 'binary_location' in config:
            # 浏览器路径设置
            binary = FirefoxBinary(config['binary_location'])
            params['firefox_binary'] = binary
        self.set_driver_params(params)
        return Firefox(**params)

    '''以远程端口调试启动本浏览器
    "C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222
    '''
    def start_browser_by_remote_debugger(self):
        config = self.config
        msg = "本地浏览器无法开启远程调试模式: "
        if "binary_location" not in config:
            msg += "binary_location 未配置，"
            raise RuntimeError(msg)
        if "debugger_address" not in config:
            msg += "debugger_address 未配置"
            raise RuntimeError()

        if config["debugger_address"].strip() == "":
            raise ValueError('debugger_address 不能为空')

        address = config['debugger_address'].split(':')
        port = address[1]

        if Socket.check_port_used(int(port)):
            print("远程调试端口:" + address[1] + "已监听成功...")
        else:
            arguments = self.config['arguments']
            start_args = []
            for arg in arguments:
                # if arg.startswith('--user-data-dir'):
                #     arg_info = arg.split('=')
                #     data_dir = arg_info[1]
                #     data_dir = Config.get_dir_path_or_mkdir(data_dir)
                #     arg = '--user-data-dir=' + data_dir
                start_args.append(arg)
            print(start_args)
            exe_content = "\"" + config['binary_location'] + "\" " + " ".join(start_args)
            print("exe_content = " + exe_content)
            # 创建子进程 os.system 改为 os.popen
            exe_result = os.popen(exe_content)
            # print(exe_result.read())
            print('本地谷歌浏览器的远程调试模式启动成功！=================OK===')

    def get_driver(self):
        print('===========Selenium WebDriver ======================= Init: ')
        print(self.config)
        driver_name = self.config['driver_browser']
        driver_map = {
            self.DRIVER_CHROME: self.get_chrome_driver,
            self.DRIVER_FIREFOX: self.get_firefox_driver
        }
        return driver_map[driver_name]()


if __name__ == '__main__':
    opts = ChromeOptions()
    driver = Chrome(options=opts)
