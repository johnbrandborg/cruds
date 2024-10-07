Interfaces
==========

Within CRUDs pre-configured Interfaces have been created.  To use an Interface
import them from interface packages under `cruds.interfaces.<name>`.

Currently available:

 - Planhat - https://docs.planhat.com/

Planhat SDK
-----------

Example:
    >>> from cruds.interfaces.planhat import Planhat
    >>>
    >>> planhat = Planhat(api_token="9PhAfMO3WllHUmmhJA4eO3tJPhDck1aKLvQ5osvNUfKYdJ7H")
    >>>
    >>> help(planhat)
