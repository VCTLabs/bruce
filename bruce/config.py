import os

import pyglet

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
    defaults = dict(
        bgcolor = (0, 0, 0, 255),
        charset = 'ascii',
        logo = None,
    )

    def set(self, key, val):
        # XXX update to use type not old value
        if key in self:
            old = self[key]
        elif key in self.defaults:
            old = self.defaults[key]
        else:
            self[key] = val
            return

        if isinstance(old, int):
            val = int(val)
        elif isinstance(old, float):
            val = float(val)
        elif isinstance(old, tuple):
            # a color
            val = tuple([int(x.strip())
                    for x in val.strip('()').split(',')])
            if len(val) < 4:
                val += (255,)
        elif isinstance(old, basestring) or old is None:
            pass
        else:
            raise ValueError("don't understand old value type %r"%(old))
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
        for k in options:
            self.defaults['%s.%s'%(name, k)] = options[k]

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

