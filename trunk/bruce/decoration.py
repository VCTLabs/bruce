import os

import pyglet
from pyglet.gl import *

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

class Decoration(dict):
    '''
    Decoratio content consists of lines of drawing commands:

    image:filename;halign=right;valign=bottom
    quad:Crrr,ggg,bbb;Vx1,y1;Vx2,y2;Vx3,y3;Vx4,y4

    Quad vertex color carries over if it's not specified for each vertex,
    allowing either solid color or blending.

    Vertexes may be expressions (which will be eval()'ed). The expressions have
    the variables "w" and "h" available which are the width and height of the
    presentation viewport.

    '''
    def __init__(self, content, **kw):
        self['bgcolor'] = (255, 255, 255, 255)
        self.content = content
        self.update(kw)

    def on_enter(self, viewport_width, viewport_height):
        self.viewport_width, self.viewport_height = viewport_width, viewport_height

        self.decorations = []
        self.batch = pyglet.graphics.Batch()

        # vars for the eval
        loc = dict(w=viewport_width, h=viewport_height)

        from bruce import resource

        # parse content
        for line in self.content.splitlines():
            if line.startswith('image:'):
                image = line.split(':')[1]
                if ';' in image:
                    fname, args = image.split(';', 1)
                else:
                    fname = image
                s = pyglet.sprite.Sprite(resource.loader.image(fname), batch=self.batch)
                # XXX use args to align
                s.x = viewport_width - s.width
                s.y = 0
                self.decorations.append(s)
            elif line.startswith('quad:'):
                quad = line.split(':')[1]
                cur_color = None
                c = []
                v = []
                for entry in quad.split(';'):
                    if entry[0] == 'C':
                        cur_color = map(int, entry[1:].split(','))
                    elif entry[0] == 'V':
                        if cur_color is None:
                            raise ValueError('invalid quad spec %r: needs color first'%quad)
                        c.extend(cur_color)
                        v.extend([eval(e, {}, loc) for e in entry[1:].split(',')
                            if '_' not in e])
                q = self.batch.add(4, GL_QUADS, QuadGroup(), ('c4B', c), ('v2i', v))
                self.decorations.append(q)
            elif line.startswith('bgcolor:'):
                self['bgcolor'] = map(int, line.split(':')[1].split(','))

    def on_leave(self):
        for decoration in self.decorations:
            decoration.delete()
        self.batch = None

    __logo = None
    def draw(self):
        # set the clear color which is specified in 0-255 (and glClearColor
        # takes 0-1)
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glClearColor(*self['bgcolor'])
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

