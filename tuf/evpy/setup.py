#! /usr/bin/env python

"""
setup.py

Written by Geremy Condra
Licensed under MIT License
Released 22 March 2010

simple setup file for evpy.
"""

from distutils.core import setup

setup(name='evpy',
	version='0.0',
	description="ctypes interface to OpenSSL's EVP library",
	author='Geremy Condra',
	author_email='debatem1@gmail.com',
	url='http://gitorious.org/evpy',
	packages=['evpy'],
	)
