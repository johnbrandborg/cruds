import importlib
import logging
import os
from typing import Any

from jsonschema import validate
import yaml


logger = logging.getLogger(__name__)

DEFAULT_INTERFACE_CONF = f"{os.path.dirname(__file__)}/interfaces.yaml"
INTERFACE_SCHEMA = f"{os.path.dirname(__file__)}/interfaces_schema.yaml"


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
    if config["version"] == 1:
        for api in config.get("api") or []:
            interface_code = importlib.import_module(api["package"])
            models: dict[str, object] = {}

            for model in api.get("models") or []:
                method_list: list[str] = []

                if api.get("required_model_methods"):
                    method_list += api["required_model_methods"]

                # Method declaration priority order.  Default is only used
                # if the model doesn't have it.
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
            Interface.__doc__ = api.get("docstring")
            globals()[api["name"]] = Interface

            del Interface


def load_config(config_file: str) -> None:
    """
    Request the creation of Interface classes using the configuration file.
    """
    with open(config_file) as cfile:
        config = yaml.safe_load(cfile)

    with open(INTERFACE_SCHEMA) as sfile:
        config_schema = yaml.safe_load(sfile)

    logger.warning("Validating configuration schema")
    validate(instance=config, schema=config_schema)

    _create_interfaces(config)


load_config(DEFAULT_INTERFACE_CONF)
