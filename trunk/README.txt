---------------------------
Bruce the Presentation Tool
---------------------------

Bruce, the Presentation Tool is for people who are tired of
fighting with presentation tools. Presentations are composed
(edited) in plain text files. It allows text, code, image,
interative Python sessions and video. It uses pyglet to render
in OpenGL.

Please REMOVE any previous installation of Bruce if you're upgrading
from prior to version 3.0!

Changes in this release:

- add support for arbitrary display elements via ``.. plugin::``
- fixed display of code blocks in absence of Pygments


Bruce, the Presentation Tool Features
=====================================

- displays reStructuredText content with one page per section or transition
- has a "bullet mode" which displays one page per *bullet point*
- handles of *most* of reStructuredText, including:

  * inline markup for emphasis, strong and literal
  * literal and line blocks
  * tables (no row or column spanning yet)
  * block quotes
  * definition, bullet and enumerated lists (including nesting and
    optional gradual expose)
  * images - inline and stand-alone, including scaling
  * page titles (section headings)

- some extensions to reStructuredText:

  * embedded Python interative interpreter sessions
  * code blocks with syntax highlighting (requires optional Pygments install)
  * videos (embedded just like images) with optional looping
  * stylesheet and layout changes on the fly (eg. multiple fonts
    per page)
  * transitions between pages
  * plugins to create your own inline elements

- page layout and decorations
- scrolling of content larger than a screenful
- sensible resource location (images, video, sound from the same directory
  as the presentation file)
- recording of timing and screenshots
- playback of previous recording or a constant speed, with optional looping
- timer and page count display for practicing
- control which screen to open on in multihead
- run fullscreen at native resolution
- may switch to/from fullscreen quickly


Installation
============

Bruce requires Python 2.5 or later to be installed on your system. Obtain
it from <http://www.python.org/>.

Please download the Bruce version for your operating system from
<http://pypi.python.org/pypi/bruce>:

- Linux "bruce-<version>-linux.zip" (eg. "bruce-3.1-linux.zip")
- Windows "bruce-<version>-windows.zip" (eg. "bruce-3.1-windows.zip")
- OS X "bruce-<version>-osx.zip" (eg. "bruce-3.1-osx.zip")

Unzip the application and double-click the "bruce" program in the created
folder. The program may be shown with a ".sh" or ".pyw" extension. Linux
users may choose to run the program in a terminal.

If the application does not work and you're on Linux you may need to
install an optional python tkinter package. This is usually achieved
by invoking something like::

   sudo apt-get install python-tk

If you are a *system package maintainer* then please read the INSTALL.txt
contained in the *source* distribution "bruce-<version>.tar.gz" or the
Subversion repository at <http://bruce-tpt.googlecode.com/svn/trunk>


How to use Bruce, the Presentation Tool
=======================================

On Windows you may just double-click the "run_bruce.py" file.

On other platforms run::

    % bruce [presentation source.txt]

If you've not installed Bruce then you may run from the source::

    % python run_bruce.py [presentation source.txt]

There's a number of command-line controls - use ``bruce -h`` to
learn what they do. With no command-line arguments Bruce will pop
up a simple GUI.


Controls
========

When running a presentation the following controls are active:

left, right arrows; left, right mouse button; space bar (forward)
  Move back and forward pages. If the page contains a list and list-expose
  has been enabled then each list item will be exposed in turn before the
  next page is displayed.
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
control-S
  Save a screenshot as "screenshot-<random number>.png" in the current
  directory.
escape
  Exit presentation
home, end
  Go to the first or last page


How to write presentations using Bruce, the Presentation Tool
=============================================================

Bruce presentations are written as plain-text files in the
reStructuredText format with some extensions. See the examples
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

and so on. For more information see the HOWTO__ (also available
online at the Bruce website) and the optional extra examples
download from <http://pypi.python.org/pypi/bruce>.

__ http://r1chardj0n3s.googlepages.com/howto


Automatic Playback
==================

Bruce has facilities for recording and playing back presentations.

The ``--record`` command-line option causes Bruce to write screenshots of each
page and timing information to the directory specified. For example if
you run::

   python run_bruce examples/test_images.rst --record=/tmp/test_images

then once you've run through the presentation you'll find Bruce has
populated ``/tmp/test_images`` with::

    /tmp/test_images/screenshot-0.png
    /tmp/test_images/screenshot-1.png
    /tmp/test_images/screenshot-2.png
    /tmp/test_images/screenshot-3.png
    /tmp/test_images/timing.txt

Where the contents of timing.txt are a timestamp (in seconds) and the
screenshot displayed at that time::

    1231803728.3 screenshot-0.png
    1231803731.9 screenshot-1.png
    1231803733.4 screenshot-2.png
    1231803738.9 screenshot-3.png

There's a few options for automatically playing a presentation:

**Playing back a recording**
  You may play back the recording captured by using the ``--playback``
  command-line option. Supply it the location of a ``timing.txt`` file as
  generated by ``--record``.

  The times in ``timing.txt`` could also start at 0 and that the
  screenshot filenames are ignored by ``--playback`` (it quite happily accepts a
  file with just times) so the following is equivalent to the timing.txt from
  above as far as playback is concerned::

    0
    2.9
    5.4
    10.9

**Constant-speed playback**
  If you just want to display each page in a presentation at a constant speed
  (like a slide show) then you may use the ``--playspeed`` command-line option.
  This gives a delay in seconds to pause bewteen each page.

  The playback speed will take page transitions into account - the delay starts
  from the start of the transition.

**Looping**
  If you wish for your automitically-played presentation to loop then use the
  ``--loop`` command-line option.

**Only play once**
  If you wish for your automitically-played presentation to quit after playing
  through once use the ``--once`` command-line option.

**Automatically capture a screenshot of every page**
  You may combine ``--record`` and ``--playspeed`` to automatically page
  through the presentation and capture a screenshot of each page. Use
  something like::

    python run_bruce.py examples/test_image.rst --record=/tmp/test_images \
          --playspeed=.5

  You'll want to make sure the presentation has::

    .. style:: :transition.name: none

  at the top. Using a speed faster than .5 is discouraged until some
  fine-tuning of timing can be done.


License
=======

Copyright (c) 2005-2009 Richard Jones <richard@mechanicalcat.net>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

