.. _interfaces:

Interfaces
==========

Within CRUDs pre-configured Interfaces have been created.  To use an Interface
import them from interface packages under `cruds.interfaces.<name>`.

Currently available:

 - Planhat

Planhat
-------

Planhat is customer success platform with imense capabilities.  CRUDs offers a
full implementation of the Planhat platform as an Interfaces.

Once you have a Planhat client create be sure to look at the comprehensive
documentation on the instances.

Official Documentation URL: https://docs.planhat.com/

Example:
    >>> from cruds.interfaces.planhat import Planhat
    >>>
    >>> planhat = Planhat(api_token="9PhAfMO3WllHUmmhJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H")
    >>> help(planhat)
    >>>
    >>> asset = planhat.asset.get_by_id("extid-21432948")

The configuration file for this Interface can be found on
`Github <https://github.com/johnbrandborg/cruds/blob/main/src/cruds/interfaces/planhat/configuration.yaml>`_.
