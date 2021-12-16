from service.Singleton import Singleton
import threading


class MyThread(threading.Thread):

    args = []
    kwargs = {}

    def __init__(self, thread_id, name, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        print("开始线程：" + self.name)
        self.func(*self.args, **self.kwargs)


class SThread(Singleton):

    thread_list = []

    def create_task(self, func, *args, **kwargs):
        task_index = len(self.thread_list) + 1
        task_name = "t" + str(task_index)
        tt = MyThread(task_index, task_name, func, *args, **kwargs)
        self.thread_list.append(tt)
        return tt

    def run_task(self, func, *args, **kwargs):
        tt = self.create_task(func, *args, **kwargs)
        tt.start()
