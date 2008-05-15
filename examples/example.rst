.. style::
   :layout.valign: center
   :align: center
   :font_size: 64

**Welcome to Bruce!**

.. style::
   :font_size: 32

Bruce the Presentation Tool version 3.0, that is

----

.. video:: examples/tada.avi

Page 1
------

.. decoration::
   bgcolor:235,235,235,255
   image:pyglet-trans-64.png;align=right;valign=bottom
   quad:C255,210,200,255;V0,h;V0,h-48;Vw,h-48;Vw,h
   quad:C255,210,200,255;V0,0;V0,64;C0,0,0,255;Vw,64;Vw,0
   viewport:0,64,w,h-(64+48)

.. style::
   :layout.valign: top
   :align: left

Line of para.
Second line of para.

Some *italic* |biohazard| **bold** text

.. |biohazard| image:: examples/biohazard.png
.. image:: examples/pyglet.png

Some more |biohazard| **bold** text.

:foo: bar
      more bar
      even more bar

.. style::
   :default.font_name: Times New Roman

Page 2
------

- bullet 1
- bullet 2

1. And you could have a whole damn ESSAY in here. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
2. item 2
3. item 3

----

.. style::
   :layout.valign: center
   :align: center

page with no title

More
----

.. style::
   :layout.valign: bottom
   :align: left

i.   foo
ii.  bar
iii. fleb
iv.  baz

Example::

  print 'hello, world!'
  def foo():
    return 'foo'

