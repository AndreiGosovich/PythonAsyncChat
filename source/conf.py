# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..", 'Chat')))
sys.path.insert(0, os.path.abspath(os.path.join("..", 'Chat', 'Client')))
# sys.path.insert(0, os.path.abspath(os.path.join("..", 'Chat', 'log')))
sys.path.insert(0, os.path.abspath(os.path.join("..", 'Chat', 'Server')))
path = os.path.abspath(os.path.join(".."))
sys.path.append(path)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Chat'
copyright = '2023, Andrei'
author = 'Andrei'
release = '1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
