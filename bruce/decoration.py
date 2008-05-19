import os

from docutils.parsers.rst import directives
from docutils import nodes

import pyglet
from pyglet.gl import *

from bruce.color import parse_color

#
# Decoration directive
#
class decoration(nodes.Special, nodes.Invisible, nodes.Element):
    def get_decoration(self):
        return self.rawsource

def decoration_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ decoration('\n'.join(content)) ]
decoration_directive.arguments = (0, 0, 0)
decoration_directive.content = True
directives.register_directive('decoration', decoration_directive)

class QuadGroup(pyglet.graphics.Group):
    def __init__(self, blend_src=GL_SRC_ALPHA, blend_dest=GL_ONE_MINUS_SRC_ALPHA,
            parent=None):
        super(QuadGroup, self).__init__(parent)
        self.blend_src = blend_src
        self.blend_dest = blend_dest

    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glBlendFunc(self.blend_src, self.blend_dest)

    def unset_state(self):
        glPopAttrib()

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.parent is other.parent and
                self.blend_src == other.blend_src and
                self.blend_dest == other.blend_dest)

    def __hash__(self):
        return hash((id(self.parent), self.blend_src, self.blend_dest))

YES_VALUES = set('yes y on true'.split())

class Decoration(object):
    '''
    Decoration content consists of lines of configuration or drawing commands::

        bgcolor: <color spec>
        title:x,y;halign;valign;font_name;font_size;bold;italic;color
        image:filename;halign=right;valign=bottom
        quad:C<color spec>;Vx1,y1;Vx2,y2;Vx3,y3;Vx4,y4

    Quad vertex color carries over if it's not specified for each vertex,
    allowing either solid color or blending.
 
    XXX allow expressions to reference the title's position and dimensions

    Colors are specified in HTML format with either three or four channels (if three
    then the fourth, alpha channel is set to 255).

    Vertexes may be expressions (which will be eval()'ed). The expressions have
    the variables "w" and "h" available which are the width and height of the
    presentation viewport.

    The default "title" is::

        title:w//2,h;center;top;Arial;28;yes;no;0,0,0,255

    (black bold 28pt Arial positioned at the top-center of the viewport)

    '''
    bgcolor = (255, 255, 255, 255)
    default_title_style = ('w//2,h', 'center', 'top', 'Arial', '28', 'yes',
        'no', 'black')

    def __init__(self, content, title=None):
        self.content = content
        self.title = title

    def copy(self):
        '''Don't copy the title.
        '''
        return Decoration(self.content, self.title)

    def get_viewport(self):
        '''A decoration may specify a smaller viewport than the total
        available. This allows for borders etc which are not overdrawn.
        '''
        return self.limited_viewport

    def on_enter(self, viewport_width, viewport_height):
        self.viewport_width, self.viewport_height = viewport_width, viewport_height
        self.limited_viewport = (0, 0, viewport_width, viewport_height)

        self.decorations = []
        self.images = []
        self.batch = pyglet.graphics.Batch()

        # vars for the eval
        self.title_style = self.default_title_style

        # parse content
        for line in self.content.splitlines():
            directive, rest = line.split(':', 2)
            getattr(self, 'handle_%s'%directive.strip())(rest.strip())

        # handle rendering the title if there is one
        if self.title is not None:
            pos, halign, valign, name, size, bold, italic, color = self.title_style

            # create the title positioning
            loc = dict(w=self.viewport_width, h=self.viewport_height)
            x, y = [eval(e, {}, loc) for e in pos.split(',') if '_' not in e]
            size = int(size)
            bold = bold.lower() in YES_VALUES
            italic = italic.lower() in YES_VALUES
            color = parse_color(color)
            l = pyglet.text.Label(self.title, name, size, bold, italic, color,
                x, y, halign=halign, valign=valign, batch=self.batch)
            self.decorations.append(l)

            if self.limited_viewport == (0, 0, viewport_width, viewport_height):
                self.limited_viewport = (0, 0, viewport_width, viewport_height -
                    l.content_height)


    def handle_image(self, image):
        halign='left'
        valign='bottom'
        if ';' in image:
            fname, args = image.split(';', 1)
            for arg in args.split(';'):
                k, v = [e.strip() for e in arg.split('=')]
                if k == 'halign': halign=v
                elif k == 'valign': valign=v
        else:
            fname = image

        image = pyglet.resource.image(fname)
        s = pyglet.sprite.Sprite(image, x=0, y=0, batch=self.batch)
        if halign == 'center':
            s.x = self.viewport_width//2 - s.width//2
        elif halign == 'right':
            s.x = self.viewport_width - s.width
        if valign == 'center':
            s.y = self.viewport_height//2 - s.height//2
        elif valign == 'top':
            s.y = self.viewport_height - s.height
        self.images.append(s)

    def handle_quad(self, quad):
        cur_color = None
        c = []
        v = []
        loc = dict(w=self.viewport_width, h=self.viewport_height)
        for entry in [e.strip() for e in quad.split(';')]:
            if entry[0] == 'C':
                cur_color = parse_color(entry[1:])
            elif entry[0] == 'V':
                if cur_color is None:
                    raise ValueError('invalid quad spec %r: needs color first'%quad)
                c.extend(cur_color)
                v.extend([eval(e, {}, loc) for e in entry[1:].split(',')
                    if '_' not in e])
        q = self.batch.add(4, GL_QUADS, QuadGroup(), ('c4B', c), ('v2i', v))
        self.decorations.append(q)

    def handle_bgcolor(self, color):
        self.bgcolor = parse_color(color)

    def handle_viewport(self, viewport):
        loc = dict(w=self.viewport_width, h=self.viewport_height)
        self.limited_viewport = tuple(eval(e, {}, loc)
            for e in viewport.split(',') if '_' not in e)

    def handle_title(self, title):
        self.title_style = line.split(':')[1].split(';')

    def on_leave(self):
        for decoration in self.decorations:
            decoration.delete()
        self.batch = None

    def draw(self):
        # set the clear color which is specified in 0-255 (and glClearColor
        # takes 0-1)
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glClearColor(*self.bgcolor)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPopAttrib()

        self.batch.draw()

    @classmethod
    def as_html(cls, content, **kw):
        return ''

    @classmethod
    def as_page(cls, content, **kw):
        from bruce.config import config
        config['decoration'] = cls(content, **kw)
        return None

