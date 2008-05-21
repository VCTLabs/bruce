import sys
import code

from docutils import nodes
from docutils.parsers.rst import directives

import pyglet
from pyglet.gl import *

#
# Python Interpreter directive
#
class interpreter(nodes.Special, nodes.Invisible, nodes.Element):
    def get_interpreter(self):
        # XXX allow to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if self.has_key('width'):
            kw['width'] = int(self['width'])
        if self.has_key('height'):
            kw['height'] = int(self['height'])
        if self.has_key('sysver'):
            kw['sysver'] = True

        return InterpreterElement(self.rawsource, **kw)

def interpreter_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ interpreter('\n'.join(arguments), **options) ]
interpreter_directive.arguments = (0, 0, 0)
interpreter_directive.options = dict(
     width=directives.positive_int,
     height=directives.positive_int,
     sysver=directives.flag,
)
interpreter_directive.content = True
directives.register_directive('interpreter', interpreter_directive)

class MyScrollableTextLayoutGroup(pyglet.text.layout.ScrollableTextLayoutGroup):
    scissor_offset_x = 0
    scissor_offset_y = 0
    view_offset_x = 0
    view_offset_y = 0
    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT | GL_SCISSOR_BIT | GL_CURRENT_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Disable scissor to check culling.
        glEnable(GL_SCISSOR_TEST)
        ox = self.scissor_offset_x + self.view_offset_x
        oy = self.scissor_offset_y + self.view_offset_y
        print ox, oy, (ox + self._scissor_x - 1,
                  oy + self._scissor_y - self._scissor_height,
                  self._scissor_width + 1,
                  self._scissor_height)
        glScissor(ox + self._scissor_x - 1,
                  oy + self._scissor_y - self._scissor_height,
                  self._scissor_width + 1,
                  self._scissor_height)
        glTranslatef(self.translate_x, self.translate_y, 0)


class ScrolledIncrementalTextLayout(pyglet.text.layout.IncrementalTextLayout):
    def _init_groups(self, group):
        # Scrollable layout never shares group becauase of translation.   
        self.top_group = MyScrollableTextLayoutGroup(group)
        self.background_group = pyglet.graphics.OrderedGroup(0, self.top_group)
        self.foreground_group = pyglet.text.layout.TextLayoutForegroundGroup(1, self.top_group)
        self.foreground_decoration_group = \
            pyglet.text.layout.TextLayoutForegroundDecorationGroup(2, self.top_group)


class InterpreterElement(pyglet.text.document.InlineElement):
    def __init__(self, content, width=400, height=200, sysver=False):
        self.width = 600
        self.height = 300
        self.content = 'Inner content\nover\nmultiple\nlines'
        super(InterpreterElement, self).__init__(self.height, 0, self.width)

    def on_enter(self, w, h):
        # format the code
        self.document = pyglet.text.document.FormattedDocument(self.content)
        self.document.set_style(0, len(self.document.text), {
            'font_name': 'Courier New',
            'font_size': 20, 
            'color': (0, 0, 0, 255),
        })

    def place(self, layout, x, y):
        self.quad = layout.batch.add(4, GL_QUADS, layout.top_group,
            ('c4B', (220, 220, 220, 255)*4),
            ('v2i', (x, y, x, y+self.height, x+self.width, y+self.height, x+self.width, y))
        )
        self.layout = ScrolledIncrementalTextLayout(self.document,
            self.width, self.height, multiline=True, batch=layout.batch,
            group=layout.top_group)
        self.layout.top_group.scissor_offset_x = -x
        self.layout.top_group.scissor_offset_y = -y
        self.layout.begin_update()
        self.layout.x = x
        self.layout.y = y
        self.layout.valign = 'bottom'
        self.layout.end_update()

    def remove(self, layout):
        self.layout.delete()
        self.quad.delete()

