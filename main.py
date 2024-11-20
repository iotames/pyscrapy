from service import Config, DB, Exporter
from models import Run
import os, sys


Config.get_instance(os.getenv("ROOT_PATH", os.path.dirname(__file__)))
DB.get_instance(Config.get_database())

def runarg(args: list):
    print(args)
    runarg = sys.argv[1]
    if runarg == "init":
        db = DB.get_instance()
        Run.create_all_tables(db.get_db_engine())
    if runarg == "debug":
        debug()

def debug():
    print(Config.get_instance().get_root_path())
    Exporter.debug()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        runarg(sys.argv)