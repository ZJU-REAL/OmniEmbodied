# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'OmniEmbodied'
copyright = '2024, OmniEmbodied Team'
author = 'OmniEmbodied Team'
release = '1.0.0'
version = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'myst_parser',
]

# Enable autosummary
autosummary_generate = True
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# MyST settings
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "colon_fence",
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_context = {
    "display_github": True,
    "github_user": "ZJU-REAL",
    "github_repo": "OmniEmbodied",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': '',
    'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files
latex_documents = [
    ('index', 'omniembodied.tex', 'OmniEmbodied Documentation',
     'OmniEmbodied Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    ('index', 'omniembodied', 'OmniEmbodied Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    ('index', 'OmniEmbodied', 'OmniEmbodied Documentation',
     author, 'OmniEmbodied', 'Embodied AI Simulation and Evaluation Platform.',
     'Miscellaneous'),
]

# -- Intersphinx mapping -----------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# -- Todo extension ----------------------------------------------------------
todo_include_todos = True

# -- Mock imports for documentation build ------------------------------------
# Mock imports for modules that cannot be imported during docs build
autodoc_mock_imports = [
    'llm',
    'llm.llm_factory',
    'llm.api_llm',
    'llm.base_llm',
    'llm.vllm_llm',
    'core',
    'modes',
    'modes.single_agent',
    'modes.centralized', 
    'modes.decentralized',
    'config',
    'evaluation',
    'data_generation',
    'utils',
]

# Autosummary configuration
autosummary_generate = False  # Disable automatic generation to avoid import errors 