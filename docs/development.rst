.. _development:

Development
===========

At this time because the CRUDs code base is located on a repository not located
under an Organization, to contribute it is recommended that you create a fork of
CRUDs and then `Create a PR <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_
from there.

Setup
-----

It is highly recommended to create a virtual environment of Python.  There are
multiple ways to do this.  The standard way is using Pythons very own
`venv <https://docs.python.org/3/library/venv.html>`_.

Once you have a forked the CRUD repository and obtained a local copy of the
source code use the develop target to install the package in edit mode and the
extra packages used for development.

.. code-block:: console

    $ cd cruds
    $ make develop

The reason for using the Makefile is that the targets within it are also used by
the Github Actions when testing, and linting.  By making these available on the
command line it's easy to run the same commands and ensure everything passes before
commiting the code.

To display the menu of the Makefile, run ``make`` with no target (argument).

.. tip::

    If you don't use Make you can run the commands manually, by opening the Makefile
    and copying the commands under the relevant targets into a terminal.
