import os


import pyglet
from pyglet.gl import *

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
        glob = {}
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
                        v.extend([eval(e, glob, loc) for e in entry[1:].split(',')])
                q = self.batch.add(4, GL_QUADS, None, ('v2i', v), ('c4b', c))
                self.decorations.append(q)

    def on_leave(self):
        for decoration in self.decorations:
            decoration.delete()
        self.batch = None

    __logo = None
    def draw(self):
        # set the clear color which is specified in 0-255 (and glClearColor
        # takes 0-1)
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        clear_color = [int(v)/255. for v in self['bgcolor'].split(',')]
        glClearColor(*clear_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPopAttrib()

        self.batch.draw()

    @classmethod
    def as_html(cls, content, **kw):
        return ''

    @classmethod
    def as_page(cls, content, **kw):
        config['decoration'] = cls(content, **kw)
        return None

class _Section(object):
    '''Each page created will grab a _Section for itself which also
    takes a snapshot of the configuration at that point.
    '''
    def __init__(self, config, name):
        self.config = config.copy()
        self.name = name
    def __getitem__(self, label):
        k = '%s.%s'%(self.name, label)
        if k in self.config:
            return self.config[k]
        if label in self.config:
            return self.config[label]
        if k in self.config.defaults:
            return self.config.defaults[k]
        return self.config.defaults[label]
    def __setitem__(self, label, value):
        if self.name == 'config':
            self.config[label] = value
        else:
            self.config['%s.%s'%(self.name, label)] = value
    def update(self, d):
        for k in d:
            if self.name == 'config':
                self.config[k] = d[k]
            else:
                self.config['%s.%s'%(self.name, k)] = d[k]

class _Config(dict):
    '''Store a set of defaults (defined here and in various page
    types and then per-presentation overrides.
    '''
    types = dict(decoration=None, sound=unicode)
    defaults = dict(decoration=Decoration(''), sound='')

    def set(self, key, val):
        # XXX update to use type not old value
        if key in self:
            old = self[key]
        elif key in self.defaults:
            old = self.defaults[key]
        else:
            self[key] = val
            return

        t = self.types[key]
        if t is tuple:
            # a color
            val = tuple([int(x.strip())
                    for x in val.strip('()').split(',')])
            if len(val) < 4:
                val += (255,)
        else:
            val = t(val)
        self[key] = val

    def __contains__(self, key):
        return super(_Config, self).__contains__(key) # (lookup done in Section now) or key in self.defaults

    def __getitem__(self, key):
        if super(_Config, self).__contains__(key):
            return super(_Config, self).__getitem__(key)
        return self.defaults[key]

    def get_section(self, name):
        return _Section(self, name)

    def add_section(self, name, options):
        for k, t, v in options:
            self.types['%s.%s'%(name, k)] = t
            self.defaults['%s.%s'%(name, k)] = v

    def copy(self):
        c = _Config()
        c.update(self)
        return c

    flags = tuple([(k, str, defaults[k]) for k in defaults])
    def __call__(self, content, **kw):
        for k in kw:
            if k in self.defaults:
                # exact match on the key
                self.set(k, kw[k])
            else:
                # otherwise match all sets with this key
                for d in self.defaults:
                    if '.' in d and d.split('.', 1)[1] == k:
                        self.set(d, kw[k])
        return self

    @classmethod
    def as_html(cls, content, **kw):
        return ''

    @classmethod
    def as_page(cls, content, **kw):
        for k in kw:
            if k in cls.defaults:
                config.set(k, kw[k])
        return None

# singleton
config = _Config()

# public API
get = config.get
set = config.set
add_section = config.add_section
get_section = config.get_section
path = os.path.abspath(os.path.join(os.getcwd(), __file__))

__all__ = 'get set add_section get_section path config Decoration'.split()

