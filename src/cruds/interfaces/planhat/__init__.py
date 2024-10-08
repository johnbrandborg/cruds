import os

from cruds.interface import load_config


for name, Interface in load_config(f"{os.path.dirname(__file__)}/configuration.yaml"):
    globals()[name] = Interface
