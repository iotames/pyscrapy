"""
单例模式基类
@link https://www.cnblogs.com/huchong/p/8244279.html
"""

import time
import threading


class Singleton(object):
    _instance_lock = threading.Lock()

    meta = {}

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = cls(*args, **kwargs)
        return cls._instance


if __name__ == '__main__':
    def task(arg):
        obj = Singleton.get_instance()
        print(obj)

    for i in range(10):
        t = threading.Thread(target=task, args=[i, ])
        t.start()
    time.sleep(5)
    obj = Singleton.get_instance()
    print(obj)
