import time


class Timer:

    __ttl = 10
    __runtime_seconds = 60

    def __init__(self, task_func, start_at=0, end_at=0):
        # 2038 年问题
        self.__task = task_func
        self.__start_at = time.time() if start_at == 0 else start_at
        self.__end_at = (self.__start_at + self.__runtime_seconds) if end_at == 0 else end_at

    @staticmethod
    def now_timestamp():
        return int(time.time())

    @property
    def ttl(self):
        return self.__ttl

    @ttl.setter
    def ttl(self, secs):
        self.__ttl = secs

    @property
    def end_at(self):
        return self.__end_at

    @end_at.setter
    def end_at(self, timestamp):
        self.__end_at = timestamp

    @property
    def start_at(self):
        return self.__start_at

    @start_at.setter
    def start_at(self, timestamp):
        self.__start_at = timestamp

    def __can_run(self):
        time_int = time.time()
        if self.__start_at < time_int < self.__end_at:
            return True
        return False

    def run(self, *args):
        now_time = time.time()
        if now_time > self.__end_at:
            print("当前时间大于定时任务运行的结束时间, 任务无法开启。强制退出")
            exit()
        if now_time < self.__start_at:
            wait_ttl = self.__start_at - now_time
            print("当前时间小于定时任务开启时间,请等待" + str(wait_ttl) + "秒")
            time.sleep(wait_ttl)
        # print("等待0.5秒")
        # time.sleep(0.5)
        times = 0
        while self.__can_run():
            self.__task(*args)
            times += 1
            print(times)
            time.sleep(self.__ttl)


if __name__ == '__main__':
    def task():
        print(time.time())

    now = time.time()
    # start = now + 3
    start = now
    end = start + 10
    print(start)
    print(end)
    timer = Timer(task, start, end)
    timer.ttl = 1

    print("====now time is=" + str(time.time()))
    print("====start=" + str(timer.start_at))
    timer.run()
    print("===end=" + str(timer.end_at))
