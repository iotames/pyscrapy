import json
import os
import time


class Logger:

    __filepath = ""
    __mode = ""
    echo_msg = False

    def __init__(self, dirpath=''):
        self.__mode = 'custom'
        time_str = time.strftime("%Y%m%d", time.localtime())
        filename = self.__mode + "_" + time_str + ".log"
        if dirpath == '':
            self.__mode = 'default'
            filename = self.__mode + "_" + time_str + ".log"
            dirpath = "runtime/logs"
        filepath = dirpath + "/" + filename
        self.__filepath = filepath

    @property
    def filepath(self):
        return self.__filepath

    @filepath.setter
    def filepath(self, filepath):
        self.__filepath = filepath

    def file_exist(self):
        return os.path.isfile(self.filepath)

    def debug(self, data):
        if self.__mode == 'default':
            self.__filepath = self.__filepath.replace('default_', 'debug_')
        self.__add(data)

    def write(self, data, mode):
        if self.__mode == 'default':
            self.__filepath = self.__filepath.replace("default_", mode + "_")
        self.__add(data)

    def __add(self, data):
        dir_name = os.path.dirname(self.filepath)
        if not os.path.exists(dir_name):
            if not dir_name == '':
                os.makedirs(dir_name)
        file = open(self.filepath, "a", encoding="utf-8")

        if not type(data) is str:
            data = json.dumps(data, ensure_ascii=False)

        long_line = "=====================start========================"
        time_str = time.strftime("%Y%m%d %H:%M:%S", time.localtime())
        begin_str = time_str + long_line
        data = os.linesep + data
        input_str = begin_str + data + os.linesep  # Windows '\r\n', Linux '\n', Mac'\r'
        if self.echo_msg:
            print(data)
        file.write(input_str)
        file.close()


if __name__ == '__main__':
    logger = Logger()
    logger.filepath = "../" + logger.filepath
    favorites = ['爬山', '游泳', '羽毛球', 22, 37, 'basketball']
    demo_log = {"name": "Jon", "age": 19, "favorites": favorites}
    logger.debug(favorites)
    logger.debug(demo_log)
