#!/usr/bin/env python

from distutils.core import setup

try:
    import fontTools
except:
    print "*** Warning: defcon requires FontTools, see:"
    print "    fonttools.sf.net"



setup(name="compositor",
    version="0.2b",
    description="A simple OpenType GSUB and GPOS engine.",
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="http://code.typesupply.com",
    license="MIT",
    packages=["compositor"],
    package_dir={"":"Lib"}
)