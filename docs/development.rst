.. _development:

===========
Development
===========

Contributions are welcome! At this time because the CRUDs code base is located on
a repository not located under an Organization, to contribute it is recommended
that you create a fork of CRUDs and then `Create a PR
<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_
from there.

Setup
-----

It is highly recommended to create a virtual environment of Python.  There are
multiple ways to do this.  The standard way is using Pythons very own
`venv <https://docs.python.org/3/library/venv.html>`_.

Once you have forked the CRUDs repository and obtained a local copy of the
source code, use the develop target to install the package in edit mode and the
extra packages used for development:

.. code-block:: console

    $ cd cruds
    $ make develop

The reason for using the Makefile is that the targets within it are also used by
the Github Actions when testing and linting.  By making these available on the
command line it's easy to run the same commands and ensure everything passes before
committing the code.

To display the menu of the Makefile, run ``make`` with no target (argument).

.. tip::

    If you don't use Make you can run the commands manually, by opening the Makefile
    and copying the commands under the relevant targets into a terminal.

Running Tests
-------------

CRUDs uses `pytest <https://docs.pytest.org/>`_ for testing with coverage
reporting enabled by default:

.. code-block:: console

    $ make test

To generate an XML coverage report (used by CI):

.. code-block:: console

    $ make test-report

Code Quality
------------

Linting and formatting are handled by `Ruff <https://docs.astral.sh/ruff/>`_:

.. code-block:: console

    $ make lint
    $ make format

Static type checking is done with `ty <https://docs.astral.sh/ty/>`_:

.. code-block:: console

    $ make typecheck

Filing Issues
-------------

If you find a bug or have a feature request, please open an issue on the
`GitHub issue tracker <https://github.com/johnbrandborg/cruds/issues>`_.
When reporting bugs, include:

- Python version and OS
- CRUDs version (``python -c "import cruds; print(cruds.__version__)"``  )
- A minimal reproducible example
- The full traceback if applicable
