#! /usr/bin/env python

import sys

# hack to get around setuptools overriding the CWD
sys.path.insert(0, '.')

import bruce.html_output
bruce.html_output.main()
