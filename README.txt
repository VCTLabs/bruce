---------------------------
Bruce the Presentation Tool
---------------------------

Bruce the Presentation Tool is for programmers who are tired of fighting
with presentation tools. In its basic form it allows text, code or image
pages and even interactive Python sessions. It uses pyglet and is easily
extensible to add new page types.

Features:

- simple point-by-point text display with styling and progressive expose
- audio playback on any page, including blank ones
- interactive Python interpreter with history
- page of Python code with execution output
- code display with scrolling
- unicode escaped chars in ascii file (or any other source file encoding)
- html page display with scrolling
- image display with optional zoom to fit, title and/or caption
- video playback with optional zoom to fit, title
- configuration may be changed inside a presentation, including per-page
- sensible resource location (images, video, sound from zip files etc.)
- custom Pages via modules found in resource path
- timer and page count display for practicing
- logo display in the corner of every page
- may specify which screen to open on in multihead
- runs fullscreen at native resolution (with sensible scaling of pages)
- may switch to/from fullscreen quickly
- HTML output of pages including notes
- may display ReStructuredText files as presentations with one page
  per section


Installation
============

Bruce REQUIRES Python 2.5 and pyglet 1.1

To install Bruce, run::

    # python setup.py install


Usage
=====

Run Bruce using "python -m bruce <arguments>". Use the -h switch to get usage
help.

See HOWTO.txt for the presentation file format.


Controls
========

left, right arrows; left, right mouse button; space bar (forward)
  Move back and forward pages (and expose/hide "-" marked text lines)
page up, page down
  Move back and forward 5 pages (ignores expose/hide text lines)
mouse scroll wheel
  Scroll large code or html file contents in the page. You may also drag
  the contents up or down by dragging a left mouse button press up and
  down the screen.
control-I
  Enter / exit auto-type mode in the interactive interpreter
control-F
  Switch between fullscreen and windowed mode
escape
  Exit presentation
home, end
  Go to the first or last page


Samples
=======

See the examples directory.


License
=======

Copyright (c) 2005-2008 Richard Jones <richard@mechanicalcat.net>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

