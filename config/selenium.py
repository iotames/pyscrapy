"""
@link https://www.selenium.dev/documentation/getting_started/installing_browser_drivers/#quick-reference

selenium 无法临时变更请求头， 无法获取响应头，如响应状态码
https://blog.csdn.net/weixin_29422697/article/details/112819239

@link https://cuiqingcai.com/8397.html 下载添加Selenium到下载中间件

"""
from selenium.webdriver import Chrome, Firefox, Ie, ChromeOptions, FirefoxOptions, IeOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from config.baseconfig import BaseConfig


class Selenium(BaseConfig):

    name = 'selenium'

    DRIVER_CHROME = 'Chrome'
    DRIVER_FIREFOX = 'Firefox'
    DRIVER_EDGE = 'Edge'
    DRIVER_IE = 'Ie'

    @classmethod
    def get_driver_cls(cls, name: str):
        return cls.DRIVER_CLS_MAP[name]

    @classmethod
    def get_driver_options_cls(cls, name: str):
        return cls.DRIVER_OPTION_CLS_MAP[name]

    def get_driver(self):
        driver_name = self.get_config()['driver_browser']
        driver_cls = self.get_driver_cls(driver_name)
        driver_opts_cls = self.get_driver_options_cls(driver_name)
        options = driver_opts_cls()
        params = {'options': options}
        config = self.get_config()

        # TODO 配置优化
        if 'binary_location' in config and config['driver_browser'] == self.DRIVER_CHROME:
            options.binary_location = config['binary_location']

        if 'driver_path' in config:
            params['executable_path'] = config['driver_path']

        if config['driver_browser'] == self.DRIVER_FIREFOX and 'binary_location' in config:
            binary = FirefoxBinary(config['binary_location'])
            params['firefox_binary'] = binary

        print('===========Selenium WebDriver ======================= Init: ')
        print(params)
        # from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
        # binary = FirefoxBinary('/path/to/binary')
        # driver = Firefox(firefox_binary=binary)
        return driver_cls(**params)

    DRIVER_CLS_MAP = {
        DRIVER_CHROME: Chrome,
        DRIVER_FIREFOX: Firefox,
        # DRIVER_EDGE: Edge,  # selenium > 4.0
        DRIVER_IE: Ie
    }

    DRIVER_OPTION_CLS_MAP = {
        DRIVER_CHROME: ChromeOptions,
        DRIVER_FIREFOX: FirefoxOptions,
        # DRIVER_EDGE: EdgeOptions,  # selenium > 4.0
        DRIVER_IE: IeOptions
    }

    DEFAULT_CONFIG = {
        'driver_browser': DRIVER_CHROME,
        'timeout': 30
    }

    SAMPLE_CONFIG = {
        'driver_browser': DRIVER_CHROME,
        'driver_path': '',
        'binary_location': '/opt/apps/org.mozilla.firefox-nal/files/firefox',
        'debugger_address': '127.0.0.1:9222',
        'arguments': [
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


if __name__ == '__main__':
    opts = ChromeOptions()
    driver = Chrome(options=opts)
