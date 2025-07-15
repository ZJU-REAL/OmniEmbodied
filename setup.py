#!/usr/bin/env python3
"""
Setup script for embodied_framework package.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Embodied Framework for AI Agent Simulation"

# Read requirements from requirements.txt if it exists
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'openai',
        'pyyaml',
        'requests',
        'numpy',
        'pandas',
        'seaborn',
        'matplotlib',
        'jupyter',
        'notebook',
        'json_repair'
    ]

setup(
    name="embodied_framework",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Embodied Framework for AI Agent Simulation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/embodied_framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'black',
            'flake8',
            'mypy',
        ],
    },
    entry_points={
        'console_scripts': [
            'embodied-framework=examples.single_agent_example:main',
        ],
    },
    include_package_data=True,
    package_data={
        'embodied_framework': [
            'config/**/*',
            'data/**/*',
        ],
    },
)
