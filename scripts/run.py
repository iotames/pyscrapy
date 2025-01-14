# from scripts.spiders.vqfit import Vqfit
# from scripts.spiders.ms365 import Ms365
# from scripts.spiders.vuoriclothing import Vuoriclothing
# from scripts.spiders.manduka import Manduka
from utils.pyfile import get_attr_to_cls

def Run(name: str):
    name = name.strip().lower()
    if name == "":
        raise Exception("Usage: python main.py script [name]")
    spidercls = get_attr_to_cls('name', 'scripts.spiders').get(name, None)
    if spidercls is None:
        raise Exception("Script name({}) not found!".format(name))
    print("Run script: " + name)
    # run_map[name]().run()
    spidercls().run()
    print("Done")
