from config.baseconfig import BaseConfig
import os
import json
import webbrowser
filepath = 'config' + os.sep + 'client' + ".json"
if not os.path.isfile(filepath):
    raise RuntimeError('{} : 文件不存在'.format(filepath))
file_stream = open(filepath, 'r', encoding='utf-8')
data: dict = json.load(file_stream)
url = data.get('start_url')

if __name__ == '__main__':
    webbrowser.open(url)
