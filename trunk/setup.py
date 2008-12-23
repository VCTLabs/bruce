#! /usr/bin/env python
#
# $Id$

from distutils.core import setup

# perform the setup action
from bruce import __version__
setup(
    name = "bruce",
    version = __version__,
    description = "Bruce, the Presentation Tool",
    long_description = '\n'.join(open('README.txt').readlines()[4:-28]),
    author = "Richard Jones",
    author_email = "richard@mechanicalcat.net",
    url = "http://r1chardj0n3s.googlepages.com/bruce",
    packages = ["bruce"],
    scripts = ['scripts/bruce'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ]
)

# vim: set filetype=python ts=4 sw=4 et si
