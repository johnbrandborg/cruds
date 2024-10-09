.. _development:

Development
===========

At this time because the CRUDs code base is located on a repository not located
under an Orgination, to contribute it is recommended that you create a fork of
CRUDs and then `Create a PR <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork>`_
from there.

Setup
-----

Once you have a forked the CRUD repository and obtained a local copy of the
source code use the develop target to install the package in edit mode and the
extra packages used for development.

.. code-block:: console

    $ cd cruds
    $ make develop

If you don't use Make you can run the commands manually, by opening the Makefile
and copying the commands under the relevant targets into a terminal.
