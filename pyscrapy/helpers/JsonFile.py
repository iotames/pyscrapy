import json
import os


class JsonFile:

    filepath = ''
    data = {}
    dataType = 'dict'

    TYPE_DICT = 'dict'
    TYPE_LIST = 'list'

    def __init__(self, filepath):
        self.filepath = filepath

    def file_exist(self):
        return os.path.isfile(self.filepath)

    def switch_type(self, datatype):
        self.dataType = datatype

    def get_empty_data(self):
        if self.dataType == self.TYPE_DICT:
            return {}
        if self.dataType == self.TYPE_LIST:
            return []

    @staticmethod
    def cookie_to_dic(cookie_text: str) -> dict:
        cookie_dic = {}
        cookie_text = cookie_text.replace(' ', '')
        # for i in cookie.split('; '):
        for i in cookie_text.split(';'):
            cookie_dic[i.split('=')[0]] = i.split('=')[1]
        return cookie_dic

    def read_cookie(self):
        # 如果文件不存在，则根据预定义的数据类型返回空数据
        if not os.path.isfile(self.filepath):
            return self.get_empty_data()
        with open(self.filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return self.cookie_to_dic(content)

    def read(self):
        # 如果文件不存在，则根据预定义的数据类型返回空数据
        if not os.path.isfile(self.filepath):
            return self.get_empty_data()
        file = open(self.filepath, "r", encoding="utf-8")
        data = json.load(file)
        self.data = data
        file.close()
        return self.data

    def write(self, data: dict):
        dir_name = os.path.dirname(self.filepath)
        if not os.path.exists(dir_name):
            if not dir_name == '':
                os.makedirs(dir_name)
        file = open(self.filepath, "w+", encoding="utf-8")
        print("打开本地文件:" + self.filepath)
        json.dump(data, file, ensure_ascii=False)
        print("写入数据: ", end=" ")
        print(data)
        file.close()
        self.data = data


if __name__ == '__main__':
    obj = JsonFile("test.json")
    print(obj.read())
