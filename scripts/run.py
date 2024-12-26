from scripts.spiders.vqfit import Vqfit
from scripts.spiders.ms365 import Ms365
from scripts.spiders.vuoriclothing import Vuoriclothing
from scripts.spiders.manduka import Manduka


run_map = {
    "vqfit": Vqfit,
    "ms365": Ms365,
    "vuoriclothing": Vuoriclothing,
    "manduka": Manduka
    }

def Run(name: str):
    name = name.strip().lower()
    if name == "":
        raise Exception("Usage: python main.py script [name]")
    if name not in run_map:
        raise Exception("Script name not found: " + name)
    print("Run script: " + name)
    run_map[name]().run()
    print("Done")
