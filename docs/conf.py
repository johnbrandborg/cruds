# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../src"))

import cruds

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CRUDs"
copyright = f"2020–{datetime.now().year}, John Brandborg"
author = "John Brandborg"
version = cruds.__version__
release = cruds.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxext.opengraph",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/johnbrandborg/cruds",
    "source_branch": "main",
    "source_directory": "docs/",
}

# -- Intersphinx mapping ----------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "urllib3": ("https://urllib3.readthedocs.io/en/stable/", None),
}

# -- Copy button settings ----------------------------------------------------

copybutton_prompt_text = r"^\$ "
copybutton_prompt_is_regexp = True

# -- Open Graph settings -----------------------------------------------------

ogp_site_url = "https://cruds.readthedocs.io/en/latest/"
ogp_description_length = 200
