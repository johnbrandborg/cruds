"""
Tests for the main Interface in CRUDs
"""

from copy import deepcopy

import pytest

import cruds.interface


@pytest.fixture
def interface():

    class Interface:
        test = cruds.interface.ModelFactory(
            docstring="Model Class",
            uri="test",
            methods={
                "echo": lambda _, x: "bar" if x == "foo" else "baz"
            },
        )

    return Interface()


def test_ModelFactory_descriptor_delete(interface):
    """
    Test that the delete magic method removes the model class which is
    recreated by get magic method
    """
    method_id = repr(interface.test)

    del interface.test

    assert repr(interface.test) != method_id


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
    assert interface.test._uri == "test"
    assert interface.test.echo("foo") == "bar"


def test__create__interface_v1_with_no_package():
    """
    Create an Interface from the factory using Version 1.
    The configuration has no package, and no listed methods.
    """
    config = {
        "api": [
            {
                "name": "TestClass",
                "docstring": "Test Class docstring",
                "detault_model_methods": [],
                "required_model_methods": [],
                "models": [],
            }
        ]
    }

    name, Interface = cruds.interface._create_interfaces_v1(config).__next__()

    assert name == "TestClass"
    assert issubclass(Interface, object)
    assert Interface.__doc__ == "Test Class docstring"

    with pytest.raises(TypeError) as e_info:
        Interface()

    assert "'NoneType' object is not callable" in repr(e_info)
