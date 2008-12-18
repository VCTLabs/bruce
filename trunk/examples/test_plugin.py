import pyglet
from pyglet.gl import *

class Element(object):
    def __init__(self, w, h):
        pass 

    def on_enter(self, w, h):
        pyglet.clock.schedule(self.tick)

    def resize(self, w, h):
        self.w, self.h = w, h
        self.descent = 0

    def place(self, layout, x, y):
        print 'PLACE', x, y, self.w, self.h
        x1 = int(x)
        y1 = int(y + self.descent)
        x2 = int(x + self.w)
        y2 = int(y + self.h + self.descent)
        self.r = layout.batch.add(4, GL_QUADS, None,
            ('c3B', (255, 0, 0) * 4),
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
        )

    def tick(self, dt):
        pass

    def remove(self, layout):
        self.r.delete()

    def on_exit(self):
        pyglet.clock.unschedule(self.tick)

