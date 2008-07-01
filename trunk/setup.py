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
    long_description = '''
Bruce, the Presentation Tool is for people who are tired of
fighting with presentation tools. Presentations are composed
(edited) in plain text files. It allows text, code, image,
interative Python sessions and video. It uses pyglet to render
in OpenGL.

Changes in this release:

- IMPORTANT: "decoration" is now called "layout"
- mention docutils requirement
- fixed page count / timer display
- allow default style to affect footer style
- display is now managed using Cocos
- add page transitions (experimental)
- nicely handle resize when switching to fullscreen
- fixed bullet symbol consistency
- fixed sub-list first item indentation
- better detection of mouse click vs. drag


Bruce, the Presentation Tool version 3.0 Features
=================================================

- displays ReStructuredText content with one page per section or transition
- handling of *most* of ReStructuredText, including:

  * inline markup for emphasis, strong and literal
  * literal and line blocks
  * block quotes
  * definition, bullet and enumerated lists (including nesting)
  * images - inline and stand-alone, including scaling
  * page titles (section headings)

- page layout and decorations
- scrolling of content larger than a screenful
- sensible resource location (images, video, sound from the same directory
  as the presentation file)
- and some extensions of ReST:

  * embedded Python interative interpreter sessions
  * videos (embedded just like images) with optional looping
  * stylesheet and layout changes on the fly (eg. multiple fonts
    per page)
  * transitions between pages

- timer and page count display for practicing
- may specify which screen to open on in multihead
- runs fullscreen at native resolution
- may switch to/from fullscreen quickly



Installation
============

Bruce REQUIRES:

- Python 2.5
- docutils 0.4.1 or later
- pyglet 1.1 beta 2 or later
- Cocos 0.3 rc0 or later

To install Bruce, run::

    # python setup.py install

How to use Bruce, the Presentation Tool
=======================================

To invoke bruce, run::

    % bruce <presentation source.txt>

There's a number of command-line controls - use ``bruce -h`` to
learn what they do.


Controls
========

left, right arrows; left, right mouse button; space bar (forward)
  Move back and forward pages.
page up, page down
  Move back and forward 5 pages.
mouse scroll wheel
  Scroll large page content. You may also drag the contents up or down
  by dragging a left mouse button press up and down the screen. If a
  page has an embedded Python Interpreter you may use the scroll-wheel
  to scroll its contents (when the mouse is over the interpreter).
  Clicking and dragging always scrolls the whole page.
control-F
  Switch between fullscreen and windowed mode
escape
  Exit presentation
home, end
  Go to the first or last page


How to write presentations using Bruce, the Presentation Tool
=============================================================

Bruce presentations are written as plain-text files in the
ReStructuredText format with some extensions. See the examples
folder \*.rst files for some samples, the simplest being
"simple.rst" which displays plain text sentences centered
on a white background (using the "big-centered" style)::

    .. load-style:: big-centered

    Text displayed centered on the default white background.

    ----

    A new page, separated from the previous using the four
    dashes.

    Ut enim ad minim veniam.

    A Page Title
    ------------

    Pages may optionally have titles which are displayed
    centered at the top by default.

and so on. For more information see the HOWTO__ at the Bruce
website and the examples directory.

__ http://r1chardj0n3s.googlepages.com/howto
''',
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
