from scripts.spiders.vqfit import Vqfit


def Run(name: str):
    if name == "":
        raise Exception("Usage: python main.py script [name]")
    if name == "vqfit":
        Vqfit().run()

