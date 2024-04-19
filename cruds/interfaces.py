import importlib
import logging
import os
from typing import Any

import yaml


logger = logging.getLogger(__name__)

DEFAULT_INTERFACE_CONF = f"{os.path.dirname(__file__)}/interfaces.yaml"


class ModelFactory:
    """
    Class Factory that is used as a descriptor
    """
    def __init__(self, docstring: str, uri: str, methods: dict) -> None:
        self.docstring = docstring
        self.uri = uri
        self.methods = methods

    def __set_name__(self, owner: object, name: str) -> None:
        self.owner = owner
        self.name = name

    def __get__(self, obj: object, objtype=None) -> Any:
        if not hasattr(self, "model"):
            Model: Any = type(self.name, (object,), {
                "_owner": obj,
                "_uri": self.uri,
                **self.methods,
            })
            Model.__doc__ = self.docstring
            self.model = Model()

        return self.model

    def __set__(self, obj, value) -> None:
        """ Read Only """
        pass


def _create_interfaces(config) -> None:
    """
    Processes the Interface configuration and creates the Interface Class.
    """
    for api in config.get("api") or []:
        name: str = api.get("name").lower()
        interface_code = importlib.import_module(
            name=f"cruds.interface_methods.{name}"
        )

        models: dict[str, object] = {}

        for model in api.get("models") or []:
            method_list: list[str] = []

            if api.get("required_model_methods"):
                method_list += api["required_model_methods"]

            method_list += (model.get("methods")
                or api.get("default_model_methods")
                or []
            )

            method_map: dict[str, object] = {
                name: interface_code.__dict__.get(name)
                for name in method_list
            }

            models[model["name"]] = ModelFactory(
                docstring=model.get("docstring"),
                uri=model.get("uri"),
                methods=method_map,
            )

        Interface: Any = type(api["name"], (object,), {
            '__init__': interface_code.__init__,
            **models,
        })
        Interface.__doc__ = api["docstring"]
        globals()[api["name"]] = Interface

        del Interface


def request(config_file: str) -> None:
    """
    Request the creation of Interface classes using the configuration file.
    """
    with open(config_file) as file:
        config = yaml.safe_load(file)

    _create_interfaces(config)


request(DEFAULT_INTERFACE_CONF)
