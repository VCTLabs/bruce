import pyglet
from pyglet.gl import *

class Element(object):
    def __init__(self, w, h):
        pass 

    def on_enter(self, w, h):
        pyglet.clock.schedule(self.tick)

    def resize(self, w, h):
        self.w, self.h = w, h

    def place(self, layout, x, y):
        c = (255, 0, 0, 255) * 4
        v = [x, y, x+self.w, y, x+self.w, y+self.h, x, y+self.h]
        self.r = layout.batch.add(4, GL_QUADS, None, ('c4B', c), ('v2i', v))

    def tick(self, dt):
        pass

    def remove(self, layout):
        self.r.delete()

    def on_exit(self):
        pyglet.clock.unschedule(self.tick)

