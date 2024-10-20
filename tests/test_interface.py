"""
Tests for the main Interface in CRUDs
"""

from copy import deepcopy
import importlib
from typing import Dict
from unittest.mock import Mock, mock_open, patch

import pytest

import cruds.interface


class Interface:
    test = cruds.interface.ModelFactory(
        docstring="Model Class",
        uri="test",
        methods={"echo": lambda _, x: "bar" if x == "foo" else "baz"},
    )


@pytest.fixture
def interface():
    class Interface:
        test = cruds.interface.ModelFactory(
            docstring="Model Class",
            uri="test_uri",
            methods={"echo": lambda _, x: "bar" if x == "foo" else "baz"},
        )

    return Interface()


def test_ModelFactory_descriptor_delete():
    """
    Test that the delete magic method removes the model class which is
    recreated by get magic method
    """
    interface = Interface()
    method_id = id(interface.test)

    del interface.test

    # assert id(interface.test) != method_id


def test_ModelFactory_descriptor_set(interface):
    """
    Test that the set magic method does nothing to the Model Class
    """
    snapshot_attributes = deepcopy(dir(interface.test))

    interface.test = "check"
    assert dir(interface.test) == snapshot_attributes
    assert interface.test.echo("foo") == "bar"


def test_ModelFactory_descriptor_setup(interface):
    """
    Test the descriptor is creating the model class and returning it
    """

    assert interface.test.__doc__ == "Model Class"
    assert interface.test._uri == "test_uri"
    assert interface.test.echo("foo") == "bar"


def test__create_interface_v1_with_no_package():
    """
    Create an Interface from the factory using Version 1.
    The configuration has no package, and no listed methods.

    With no __init__ method the created class is also not callable anymore.
    """
    config = {
        "api": [
            {
                "name": "TestClass",
                "docstring": "Test Class docstring",
            }
        ]
    }

    name, Interface = cruds.interface._create_interfaces_v1(config).__next__()

    assert name == "TestClass"
    assert issubclass(Interface, object)
    assert Interface.__doc__ == "Test Class docstring"

    with pytest.raises(TypeError) as excinfo:
        Interface()

    assert "'NoneType' object is not callable" == str(excinfo.value)


def test__create_interface_v1_with_package_and_models(monkeypatch):
    """
    Create an Interface from the factory using Version 1.
    The configuration has no package, and no listed methods.
    """

    class MockPackage:
        __dict__: Dict[str, object] = {
            "__init__": lambda _: None,
            "echo": lambda _, x: "bar" if x == "foo" else "baz",
        }

        def __init__(self, name) -> None:
            pass

    monkeypatch.setattr(importlib, "import_module", MockPackage)

    config = {
        "api": [
            {
                "name": "TestClass",
                "docstring": "Test Class docstring",
                "package": "cruds.interface.mocked",
                "models": [
                    {
                        "name": "test_model",
                        "methods": [
                            "echo",
                            "doesnt_exist",
                        ],
                    }
                ],
            }
        ]
    }

    _, TestClass = cruds.interface._create_interfaces_v1(config).__next__()

    test_instance = TestClass()

    assert test_instance.test_model.echo("foo") == "bar"

    with pytest.raises(TypeError) as e_info:
        test_instance.test_model.doesnt_exist()

    assert "'NoneType' object is not callable" == str(e_info.value)


def test_load_config_invalid_version():
    """
    Load a configuration file that has no valid version, and ensure it raises
    """
    mock_validate = Mock()
    mock_create_interface_v1 = Mock()
    mock_create_interface_v1.return_value = iter(["Version1Interface"])

    sample_config = """\
    version: 0
    """

    with patch("builtins.open", mock_open()), patch(
        "builtins.open", mock_open(read_data=sample_config)
    ), patch("cruds.interface.validate", mock_validate), pytest.raises(
        ValueError
    ) as e_info:
        cruds.interface.load_config("test_interface").__next__()

    assert "Configuration has no valid version" == str(e_info.value)


def test_load_config_version_1():
    """
    Load a configuration file and create the interfaces based on version 1
    """
    mock_validate = Mock()
    mock_create_interface_v1 = Mock()
    mock_create_interface_v1.return_value = iter(["Version1Interface"])

    sample_config = """\
    version: 1
    """

    with patch("builtins.open", mock_open()), patch(
        "builtins.open", mock_open(read_data=sample_config)
    ), patch("cruds.interface.validate", mock_validate), patch(
        "cruds.interface._create_interfaces_v1", mock_create_interface_v1
    ):
        for interface in cruds.interface.load_config("test_interface"):
            assert interface == "Version1Interface"
            mock_create_interface_v1.assert_called_once_with({"version": 1})
