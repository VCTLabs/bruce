#! /usr/bin/env python
#
# $Id$

from distutils.core import setup

# perform the setup action
from bruce import __version__
setup(
    name = "bruce",
    version = __version__,
    description = "Bruce the Presentation Tool",
    long_description = '''Bruce the Presentation Tool is for
programmers who are tired of fighting with presentation tools. In its
basic form it allows text, code or image pages and even interactive
Python sessions. It uses pyglet and is easily extensible to add new
page types.

2.0beta2 released on 2008-03-10 includes:

- add initial text expose effect (fade in)
- allow configuration to be set per-page and combine page flags and config
- pause on video EOS
- allow Pages to communicate back to Presentation through events
- custom Pages via modules found in resource path
- resources now much more tightly controlled
- add Python code + execution page (still has interactivity issues)
- more robust presentation file parser
- fix caret positioning on history navigation and in-line editing
- BrucePoint(tm) styling (bullet points, text page alignment)
- scale fonts based on the actual viewport size

Bruce 2.0 has:

- audio playback on any page, including blank ones
- simple point-by-point text display with styling and progressive expose
- interactive python interpreter with history
- code display with scrolling
- unicode escaped chars in ascii file
- html page display with scrolling
- image display with optional title and/or caption
- configuration may be changed inside a presentation, affecting subsequent pages
- resource location (images, video, sound from zip files etc.)
- timer and page count display for practicing
- logo display in the corner of every page
- may specify which screen to open on in multihead
- may switch to/from fullscreen
- HTML output of pages including notes
- video playback
''',
    author = "Richard Jones",
    author_email = "richard@mechanicalcat.net",
    url = "http://bruce.python-hosting.com/",
    packages = ["bruce"],
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
