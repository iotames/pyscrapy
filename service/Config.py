import os
from dotenv import load_dotenv
from service.Singleton import Singleton

load_dotenv()

class Config(Singleton):


    __root_path: str
    __http_proxy: str
    __images_path: str

    def __init__(self, rootpath: str):
        # print("--------init--Config---:"+rootpath)
        self.__root_path = rootpath
        self.__http_proxy = os.getenv("HTTP_PROXY", "")
        # runtime/downloads/images"
        self.__images_path = os.getenv("IMAGES_PATH", os.path.join(self.__root_path, "runtime", "downloads", "images"))
        print(f"----Init--Config---HTTP_PROXY({self.__http_proxy})---get_database({self.get_database()})--")
        super(Config, self).__init__(rootpath)
    
    def get_root_path(self) -> str:
        return self.__root_path

    def get_http_proxy(self) -> str:
        return self.__http_proxy

    def get_abspath(self, path: str):
        if path.startswith('/'):
            return path
        for disk in ['C:', 'D:', 'E:', 'F:', 'G:', 'H:']:
            if path.startswith(disk):
                return path
        return self.get_root_path() + os.path.sep + path

    def get_logs_dir(self):
        return os.path.join(self.__root_path, "runtime", "logs")
    
    def get_export_dir(self):
        return os.path.join(self.__root_path, "runtime", "exporter")
    
    def get_images_path(self):
        return self.__images_path

    @staticmethod
    def get_database() -> dict:
        return {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": os.getenv("DB_PORT", 3306),
            "username": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", "root"),
            "db_name": os.getenv("DB_NAME", "pyscrapy"),
            "db_type": os.getenv("DB_TYPE", "sqlite"),
            "db_schema": os.getenv("DB_SCHEMA", ""),
        }
