# -*- coding: utf-8 -*-

# Learn more: https://github.com/ogtega/polist_congress

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="polist_congress",
    version="0.1.0",
    description="",
    long_description=readme,
    author="Teslim Olunlade",
    author_email="tolunlade@outlook.com",
    url="https://github.com/ogtega/polist_congress",
    license=license,
    packages=find_packages(exclude=("tests", "samples")),
)
