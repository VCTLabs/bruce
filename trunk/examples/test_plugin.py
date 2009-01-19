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


class Plugin(plugin.Plugin):
    def resize(self, w, h):
        self.w, self.h = w, h

    def set_active(self, active):
        if active:
            self.group.angle = 0
            pyglet.clock.schedule(self.tick)
        else:
            pyglet.clock.unschedule(self.tick)

    def tick(self, dt):
        self.group.angle += 1
        if self.group.angle == 360:
            self.group.angle = 1

    # XXX split into create /  place / destroy
    def place(self, layout, x, y):
        x1 = int(x)
        y1 = int(y)
        x2 = int(x + self.w)
        y2 = int(y + self.h)
        self.group = TestGroup(layout.top_group)
        self.group.center = (x+self.w/2, y+self.h/2)
        self.r = layout.batch.add(4, GL_QUADS, self.group,
            ('c4B', (255, 0, 0, self.opacity) * 4),
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
        )

    def set_opacity(self, opacity):
        self.r.colors[:] = [255, 0, 0, opacity]*4

    def remove(self, layout):
        self.r.delete()

