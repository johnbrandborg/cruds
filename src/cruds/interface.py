import importlib
from logging import getLogger
import os
from typing import Any, Callable, List

from jsonschema import validate
import yaml


logger = getLogger(__name__)

INTERFACE_SCHEMA = f"{os.path.dirname(__file__)}/interface_schema.yaml"


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

    def __delete__(self, obj) -> None:
        """
        Remove the Model Class so it can be recreated.
        """
        del self.model

    def __get__(self, obj: object, objtype=None) -> Any:
        """
        Create a Model Class with the owner for client access, and the URI
        for making CRUDs to the API.
        """
        if not hasattr(self, "model"):
            Model: Any = type(
                self.name,
                (object,),
                {
                    "_owner": obj,
                    "_uri": self.uri,
                    **self.methods,
                },
            )
            Model.__doc__ = self.docstring
            self.model = Model()

        return self.model

    def __set__(self, obj, value) -> None:
        """
        Setting the attribute will do nothing.
        """
        pass


def _create_interfaces_v1(config: dict):
    """
    Processes the Interface configuration and creates the Interface Classes.
    """
    for api in config.get("api") or []:
        if package_name := api.get("package"):
            package = importlib.import_module(package_name)
            interface_code = package.__dict__
        else:
            interface_code = {}

        models: dict[str, object] = {}

        for model in api.get("models") or []:
            method_list: List[str] = []

            if api.get("required_model_methods"):
                method_list += api["required_model_methods"]

            # Method declaration priority order.  Default is only used
            # if the model doesn't have it.
            method_list += (
                model.get("methods") or api.get("default_model_methods") or []
            )

            method_map: dict[str, object] = {
                name: interface_code.get(name) for name in method_list
            }

            models[model["name"].lower()] = ModelFactory(
                docstring=model.get("docstring"),
                uri=model.get("uri"),
                methods=method_map,
            )

        interface_methods: dict[str, Callable | None] = {
            name: interface_code.get(name)
            for name in api.get("methods") or ["__init__"]
        }

        Interface: Any = type(
            api["name"],
            (object,),
            {
                **interface_methods,
                **models,
            },
        )
        Interface.__doc__ = api.get("docstring")

        yield (api["name"], Interface)


def load_config(file_name: str):
    """
    Request the creation of Interface classes using the configuration file.
    """
    with open(file_name) as config_file:
        config = yaml.safe_load(config_file)

    with open(INTERFACE_SCHEMA) as schema_file:
        config_schema = yaml.safe_load(schema_file)

    logger.info("Validating interface configuration schema")
    validate(instance=config, schema=config_schema)

    if config.get("version") == 1:
        yield from _create_interfaces_v1(config)
    else:
        # The validation should catch this situation, but added for consistency
        # and testing.
        raise ValueError("Configuration has no valid version")
