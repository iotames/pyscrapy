import sys
import uuid
import requests
import hashlib
import time
# from imp import reload
from importlib import reload
from config.translator import Translator as TransConf


class Translator:

    api_url: str
    app_key: str
    app_secret: str
    http_proxy = None
    # APP_KEY = '59c589958a12ff1c'
    # APP_SECRET = 'eNHy4KBf7DSqN8rjdMrElwWbNzbKQ7sk'

    def __init__(self):
        reload(sys)
        conf = TransConf().get_config()
        if conf.get('app_provider') == TransConf.PROVIDER_YOUDAO:
            self.api_url = 'https://openapi.youdao.com/api'
            self.app_key = conf.get('app_key')
            self.app_secret = conf.get('app_secret')
            self.http_proxy = conf.get('http_proxy')

    @staticmethod
    def __encrypt(signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()

    @staticmethod
    def __truncate(q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

    def __do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        proxies = {'https': self.http_proxy, 'http': self.http_proxy} if self.http_proxy else None
        return requests.post(self.api_url, data=data, headers=headers, proxies=proxies)

    # https://fanyi-api.baidu.com/api/trans/product/apidoc
    def trans_by_youdao(self, q: str, fro: str, to: str) -> str:
        # auto zh en yue(粤语) wyw(文言文) jp kor(韩语)
        """ free API (免费API)
        url = f"http://fanyi.youdao.com/translate?&doctype=json&type=AUTO&i={content}"
        response = requests.get(url)
        json_data = response.json()
        return json_data["translateResult"][0][0]["tgt"]
        """
        if not q:
            raise ValueError("empty string can not translate")
        data = {}
        data['from'] = fro
        data['to'] = to
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = self.app_key + self.__truncate(q) + salt + curtime + self.app_secret
        sign = self.__encrypt(signStr)
        data['appKey'] = self.app_key
        data['q'] = q
        data['salt'] = salt
        data['sign'] = sign
        # data['vocabId'] = "您的用户词表ID"

        response = self.__do_request(data)
        # contentType = response.headers['Content-Type']
        # if contentType == "audio/mp3":
        #     millis = int(round(time.time() * 1000))
        #     filePath = "合成的音频存储路径" + str(millis) + ".mp3"
        #     fo = open(filePath, 'wb')
        #     fo.write(response.content)
        #     fo.close()
        data_json: dict = response.json()
        print(data_json)
        err_code = int(data_json.get('errorCode', 0))
        if err_code != 0:
            if err_code == 202:
                print(f"err_code={str(err_code)}=====sign_fail====string bust be utf-8")
                return q
            raise RuntimeError(f"api request return errorCode: {data_json['errorCode']}")
        # for key, value in data_json.items():
        #     print(f"\n=====key======{key}=====\n")
        #     print(value)
        return data_json['translation'][0]

    def to_chinese(self, q, fro="auto"):
        return self.trans_by_youdao(q, fro, 'zh')


if __name__ == '__main__':
    q = "Running/walking/hiking, HIIT/Weightlifting/Gym, Yoga/Low intensity , Everyday Use, Other"
    trans = Translator()
    result = trans.to_chinese(q)
    print(result)


