#! /usr/bin/env python

import sys

# hack to get around setuptools overriding the CWD
sys.path.insert(0, '.')

import bruce.run
bruce.run.main()
