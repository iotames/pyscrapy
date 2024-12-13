from service import Config, DB, Exporter
from models import Run, Site
from exporter import export_spider_data
from scripts.run import Run as RunScript
import os, sys


Config.get_instance(os.getenv("ROOT_PATH", os.path.dirname(__file__)))
DB.get_instance(Config.get_database())

def runarg(args: list):
    runarg = args[1]
    db = DB.get_instance()
    if runarg == "debug":
        debug()    
    if runarg == "init":
        Run.create_all_tables(db.get_db_engine())
    if runarg == "truncate":
        Run.truncate_all_tables(db.get_db_engine())
    if len(sys.argv) > 2:
        if runarg == "script":
            # python main.py script vqfit
            RunScript(sys.argv[2])
        if runarg == "export":
            # python main.py export aybl
            export_spider_data(sys.argv[2])

def debug():
    from utils import pyfile
    print("root_path:", Config.get_instance().get_root_path())
    # Exporter.debug()
    # Site.debug()
    pyfile.debug()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        runarg(sys.argv)