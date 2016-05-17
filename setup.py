#!/usr/bin/env python

from __future__ import print_function
from setuptools import setup

try:
    import fontTools
except:
    print("*** Warning: defcon requires FontTools, see:")
    print("    github.com/behdad/fonttools")



setup(
    name="compositor",
    version="0.2b",
    description="A simple OpenType GSUB and GPOS engine.",
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="https://github.com/typesupply/compositor",
    license="MIT",
    packages=["compositor"],
    package_dir={"":"Lib"}
)
