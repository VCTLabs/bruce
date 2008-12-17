import sys
import code

from docutils import nodes
from docutils.parsers.rst import directives

import pyglet
from pyglet.gl import *

from cocos.director import director

#
# Plugin directive
#
class plugin(nodes.Special, nodes.Invisible, nodes.Element):
    '''Document tree node representing a plugin directive.
    '''
    def get_plugin(self):
        # XXX allow to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if self.has_key('width'):
            kw['width'] = int(self['width'])
        if self.has_key('height'):
            kw['height'] = int(self['height'])

        return PluginElement(self.rawsource, **kw)

def plugin_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ plugin('\n'.join(arguments), **options) ]
plugin_directive.arguments = (1, 0, 1)
plugin_directive.options = dict(
     width=directives.positive_int,
     height=directives.positive_int,
)
plugin_directive.content = True
directives.register_directive('plugin', plugin_directive)

class PluginElement(pyglet.text.document.InlineElement):
    def __init__(self, content, width=800, height=400):
        self.width_spec = self.width = width
        self.height_spec = self.height = height

        name = content + '.py'
        try:
            f = pyglet.resource.file(name)
        except pyglet.resource.ResourceNotFoundException:
            raise ValueError('plugin file %s not found'%name)

        try:
            source = f.read()
        finally:
            f.close()
        d = {}

        # XXX handle errors
        exec source in d

        if 'Element' not in d:
            raise ValueError('Element not found in %s'%name)

        self.implementation = d['Element'](self.width, self.height)

        super(PluginElement, self).__init__(self.height, 0, self.width)

    def set_scale(self, scale):
        self.width = int(self.width_spec * scale)
        self.height = int(self.height_spec * scale)

        self.implementation.resize(self.width, self.height)

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

    def on_enter(self, w, h):
        self.implementation.on_enter(w, h)

    def place(self, layout, x, y):
        self.implementation.place(layout, x, y)

    def remove(self, layout):
        self.implementation.remove(layout)

    def on_exit(self):
        self.implementation.on_exit()

    
