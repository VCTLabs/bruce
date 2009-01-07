import pyglet
from pyglet.gl import *

from bruce import plugin

class TestGroup(pyglet.graphics.Group):
    angle = 0

    def set_state(self):
        glPushMatrix()
        x, y = self.center
        glTranslatef(x, y, 0)
        glRotatef(self.angle, 0, 0, 1)
        glTranslatef(-x, -y, 0)

        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        glPopMatrix()

        glPopAttrib()


    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.texture)

    def __eq__(self, other):
        return (other.__class__ is self.__class__ and
                self.parent is other.parent and
                self.angle == other.angle and
                self.center == other.center)

    def __hash__(self):
        return hash((id(self.parent), self.center, self.angle))

class Plugin(plugin.Plugin):
    needs_tick = True
    def resize(self, w, h):
        self.w, self.h = w, h

    def tick(self, dt):
        self.group.angle += 1

    def place(self, layout, x, y):
        x1 = int(x)
        y1 = int(y)
        x2 = int(x + self.w)
        y2 = int(y + self.h)
        self.group = TestGroup(layout.top_group)
        self.group.center = (x+self.w/2, y+self.h/2)
        self.r = layout.batch.add(4, GL_QUADS, self.group,
            ('c4B', (255, 0, 0, 255) * 4),
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
        )

    def set_opacity(self, opacity):
        self.r.colors[:] = [255, 0, 0, self.opacity]*4

    def remove(self, layout):
        self.r.delete()

