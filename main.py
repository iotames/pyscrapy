from models import Run
from service import Config, DB
import os, sys


Config.get_instance(os.getenv("ROOT_PATH", os.path.dirname(__file__)))
print(Config.get_instance().get_root_path())

def runarg(args: list):
    print(args)
    if sys.argv[1] == "init":
        db = DB.get_instance(Config.get_database())
        Run.create_all_tables(db.get_db_engine())

def debug():
    cf1 = Config.get_instance()
    print("------cf1-----", cf1)
    cf2 = Config.get_instance()
    print("------cf2-----", cf2)


if __name__ == '__main__':
    # debug()
    if len(sys.argv) > 1:
        runarg(sys.argv)