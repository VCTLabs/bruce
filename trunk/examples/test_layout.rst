The Title, Centered
-------------------

.. style::
   :layout.background_color: silver
   :layout.viewport: 0,64,w,h-(64+48)
   :literal.background_color: #00000020

.. layout::
   :image: pyglet-trans-64.png;halign=right;valign=bottom
   :vgradient: white;#ffc0a0
   :quad: C#ffc0a0;V0,h;V0,h-48;Vw,h-48;Vw,h
   :quad: C#ffc0a0;V0,0;V0,64;Cblack;Vw,64;Vw,0

.. footer::
   a footer

Salmony bar at top behind title. Vertical gradient from white to salmon in background.
Salmony bar fading to black across the bottom, with logo on the right.

Also with a viewport to make sure we don't cover the bars.

(Try scrolling the text to make sure the viewport works)

Literal block with alpha backgruond::

    Lorem ipsum dolor sit amet.
    Consectetur adipisicing elit.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

Nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Lorem ipsum dolor sit amet.

Consectetur adipisicing elit.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

Nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.


Title right-aligned
-------------------

.. style::
   :title.position: w,h
   :title.hanchor: right
   :title.vanchor: top
   :footer.position: w,0
   :footer.hanchor: right
   :footer.vanchor: bottom
   :footer.color: white

Title right-aligned, footer right-aligned


Title left-aligned
-------------------

.. style::
   :title.position: 0,h
   :title.hanchor: left
   :title.vanchor: top
   :footer.position: 0,0
   :footer.hanchor: left
   :footer.vanchor: bottom
   :footer.color: black

Title left-aligned, footer left-aligned


red to blue down
----------------

.. layout::
   :vgradient: red;blue

Content

red to blue across
------------------

.. layout::
   :hgradient: red;blue

Content

With a big literal block::

    With lots of stuff. With lots of stuff. 
    With lots of stuff. With lots of stuff. 
    With lots of stuff. With lots of stuff. 


Test regression
---------------

.. layout::
   :bgcolor: white
   :viewport: 0,0,w,h

This page includes an old-style layout background / viewport spec which
have been replaced by stylesheet elements. Warnings should have been
generated in the console. The specific change::

    .. layout::
       :bgcolor: white
       :viewport: 0,0,w,h

becomes::

    .. style::
       :layout.background_color: white
       :layout.viewport: 0,0,w,h

