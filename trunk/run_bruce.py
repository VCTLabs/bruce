#! /usr/bin/env python

import sys

# hack to get around setuptools overriding the CWD
sys.path.insert(0, '.')

# include to allow import of roman
sys.path.insert(0, 'docutils-extras')

import bruce.run
bruce.run.main()
