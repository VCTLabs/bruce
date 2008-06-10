'''Page layout directive for Bruce pages.

Handles the directive declaration and rendering of the layout.
'''
import os

from docutils.parsers.rst import directives
from docutils import nodes

import pyglet
from pyglet.gl import *

import cocos

from bruce.color import parse_color

#
# Layout directive
#
class layout(nodes.Special, nodes.Invisible, nodes.Element):
    def get_layout(self):
        return self.rawsource

def layout_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ layout('\n'.join(content)) ]
layout_directive.arguments = (0, 0, 0)
layout_directive.content = True
directives.register_directive('layout', layout_directive)

class QuadGroup(pyglet.graphics.Group):
    ' pyglet.graphics group defining the blending operation for layout quads '
    def __init__(self, blend_src=GL_SRC_ALPHA,
            blend_dest=GL_ONE_MINUS_SRC_ALPHA, parent=None):
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

class Layout(cocos.layer.Layer):
    '''Rendering of page layouts.
    '''
    default_title_position = ('w//2,h', 'center', 'top')
    default_footer_position = ('w//2,0', 'center', 'bottom')

    def __init__(self, content, stylesheet, title=None, footer=None):
        self.content = content
        self.stylesheet = stylesheet
        self.title = title
        self.footer = footer
        super(Layout, self).__init__()

    def copy(self):
        '''Make a copy of this layout, usually to keep for a given page.
        '''
        return Layout(self.content, self.stylesheet, self.title,
            self.footer)

    def get_viewport(self):
        '''A layout may specify a smaller viewport than the total
        available. This allows for borders etc which are not overdrawn.
        '''
        return self.limited_viewport

    def on_enter(self):
        vx = vy = 0
        # scale the desired size up /down to the physical size
        ow, oh = self.parent.desired_size
        w, h = cocos.director.director.window.get_size()
        scale = self.parent.get_scale()
        vw = int(ow * scale)
        vh = int(oh * scale)
        if vw < w:
            vx = (w - vw)//2
        if vh < h:
            vy = (h - vh)//2
        self.viewport_width, self.viewport_height = vw, vh

        # set up defaults
        self.limited_viewport = (vx, vy, vw, vh)
        self.bgcolor = self.stylesheet['layout']['background_color']

        self.decorations = []
        self.images = []
        self.batch = pyglet.graphics.Batch()

        # vars for the eval
        self.title_position = self.default_title_position
        self.footer_position = self.default_footer_position

        # set up the rendering for this layout by parsing its spec
        for line in self.content.splitlines():
            directive, rest = line.split(':', 2)
            getattr(self, 'handle_%s'%directive.strip())(rest.strip())

        # detect explicit viewport limiting to avoid automatic setting below
        viewport_changed = False
        if self.limited_viewport != (vx, vy, vw, vh):
            viewport_changed = True

        # handle rendering the title if there is one
        if self.title is not None:
            # position
            pos, halign, valign = self.title_position
            loc = dict(w=vw, h=vh)
            x, y = [eval(e, {}, loc) for e in pos.split(',') if '_' not in e]

            # style
            name = self.stylesheet.value('title', 'font_name')
            size = self.stylesheet.value('title', 'font_size')
            italic = self.stylesheet.value('title', 'italic', False)
            bold = self.stylesheet.value('title', 'bold', False)
            color = self.stylesheet.value('title', 'color')
            align = self.stylesheet.value('title', 'align', 'center')

            # and create label
            l = pyglet.text.Label(self.title, name, size, bold, italic, color,
                x, y, anchor_x=halign, anchor_y=valign, halign=halign,
                dpi=int(scale*96), batch=self.batch)
            self.decorations.append(l)

            # adjust viewport restriction
            if not viewport_changed and valign == 'top':
                self.limited_viewport = (vx, vy, vw, vh - l.content_height)

        if self.footer is not None:
            # position
            pos, halign, valign = self.footer_position
            loc = dict(w=vw, h=vh)
            x, y = [eval(e, {}, loc) for e in pos.split(',') if '_' not in e]

            # label
            # XXX should only need width for this label if centering
            l = pyglet.text.DocumentLabel(self.footer, x, y, vw,
                anchor_x=halign, anchor_y=valign, multiline=True,
                dpi=int(scale*96), batch=self.batch)
            self.decorations.append(l)

            # adjust viewport restriction automatically if the footer is at the bottom
            if not viewport_changed and valign == 'bottom':
                x, y, w, h = self.limited_viewport
                footer_height = l.content_height + l.y
                if y < footer_height:
                    d = footer_height - y
                    y = footer_height
                    h -= d
                    self.limited_viewport = (x, y, w, h)

    def on_exit(self):
        for decoration in self.decorations:
            decoration.delete()
        self.batch = None

    def handle_resize(self):
        self.on_exit()
        self.on_enter()

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
                    raise ValueError(
                        'invalid quad spec %r: needs color first'%quad)
                c.extend(cur_color)
                v.extend([eval(e, {}, loc) for e in entry[1:].split(',')
                    if '_' not in e])
        q = self.batch.add(4, GL_QUADS, QuadGroup(), ('c4B', c), ('v2i', v))
        self.decorations.append(q)

    def handle_bgcolor(self, color):
        self.bgcolor = parse_color(color)

    def handle_footer_align(self, align):
        self.footer_position = line.split(':')[1].split(';')

    def handle_viewport(self, viewport):
        loc = dict(w=self.viewport_width, h=self.viewport_height)
        self.limited_viewport = tuple(eval(e, {}, loc)
            for e in viewport.split(',') if '_' not in e)

    def handle_title(self, title):
        self.title_position = line.split(':')[1].split(';')

    def draw(self):
        glPushAttrib(GL_COLOR_BUFFER_BIT)
        glClearColor(*self.bgcolor)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPopAttrib()

        self.batch.draw()

