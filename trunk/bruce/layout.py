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
    '''Document tree node representing a page layout directive.
    '''
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

class Layout(dict):
    '''Rendering of page layouts.
    '''
    def __init__(self, valign='top', background_color=(255, 255, 255, 255), viewport=None):
        self.update(
            valign=valign,
            background_color=background_color,
            viewport=viewport,
        )

        # these atributes are parsed out of the layout spec in the presentation
        # or BSS
        self.title = None
        self.footer = None
        self.quads = []
        self.images = []

    def copy(self):
        '''Make a copy of this layout, usually to keep for a given page.
        '''
        l = Layout()
        l.update(**self)
        l.title = self.title
        l.footer = self.footer
        l.quads = self.quads
        l.images = self.images
        return l

    def layer(self, stylesheet):
        return LayoutLayer(self, stylesheet)


class LayoutLayer(cocos.layer.Layer):
    def __init__(self, spec, stylesheet):
        self.spec = spec
        self.stylesheet = stylesheet

        super(LayoutLayer, self).__init__()

    def get_viewport(self):
        '''A layout may specify a smaller viewport than the total
        available. This allows for borders etc which are not overdrawn.
        '''
        return self.limited_viewport

    def create(self):
        ow, oh = self.parent.desired_size

        # figure the offset we need to center the viewport
        vx = vy = 0

        # scale the desired size up /down to the physical size
        w, h = cocos.director.director.window.get_size()
        scale = self.parent.get_scale()
        vw = int(ow * scale)
        vh = int(oh * scale)
        if vw < w:
            vx = (w - vw)//2
        if vh < h:
            vy = (h - vh)//2

        viewport = self.stylesheet.value('layout', 'viewport', None)

        if viewport:
            # scale / shift explicit viewport position and dimensions
            self.limited_viewport = [
                int(eval(e, {}, {'w':vw,'h':vh})*scale)
                    for e in viewport
                    if '_' not in e
            ]
            self.limited_viewport[0] += vx
            self.limited_viewport[1] += vy
        else:
            # set up automatic viewport initial values
            self.limited_viewport = (vx, vy, vw, vh)

        # set up rendering of the quads
        self.batch = pyglet.graphics.Batch()
        self.decorations = []

        # background
        c = tuple(self.stylesheet.value('layout', 'background_color')) * 4
        v = [vx, vy, vx+vw, vy, vx+vw, vy+vh, vx, vy+vh]
        q = self.batch.add(4, GL_QUADS, QuadGroup(), ('c4B', c), ('v2i', v))
        self.decorations.append(q)

        # quads
        for (c, v) in self.spec.quads:
            # scale and shift
            v = [int(n * scale) for n in v]
            for i in range(4):
                if vx: v[i*2] += vx
                if vy: v[i*2 + 1] += vy
            q = self.batch.add(4, GL_QUADS, QuadGroup(), ('c4B', c), ('v2i', v))
            self.decorations.append(q)

        # position images
        for fname, halign, valign in self.spec.images:
            image = pyglet.resource.image(fname)
            s = pyglet.sprite.Sprite(image, x=0, y=0, batch=self.batch)
            s.scale = scale
            if halign == 'center':
                s.x = vw//2 - s.width//2
            elif halign == 'right':
                s.x = vw - int(s.width)
            if valign == 'center':
                s.y = vh//2 - s.height//2
            elif valign == 'top':
                s.y = vh - int(s.height)
            s.x += vx
            s.y += vy
            self.decorations.append(s)

        # handle rendering the title if there is one
        if self.spec.title is not None:
            # title positioning
            pos = self.stylesheet.value('title', 'position')
            hanchor = self.stylesheet.value('title', 'hanchor')
            vanchor = self.stylesheet.value('title', 'vanchor')
            x, y = [int(eval(e, {}, {'w':vw,'h':vh}))
                for e in pos if '_' not in e]
            x += vx
            y += vy

            # style
            name = self.stylesheet.value('title', 'font_name')
            size = self.stylesheet.value('title', 'font_size')
            italic = self.stylesheet.value('title', 'italic', False)
            bold = self.stylesheet.value('title', 'bold', False)
            color = self.stylesheet.value('title', 'color')

            # and create label
            l = pyglet.text.Label(self.spec.title, name, size, bold, italic, color,
                x, y, anchor_x=hanchor, anchor_y=vanchor,
                dpi=int(scale*96), batch=self.batch)
            self.decorations.append(l)

            # adjust automatic viewport restriction if the title is at the top
            if not viewport and vanchor == 'top':
                self.limited_viewport = (vx, vy, vw, vh - l.content_height)

        if self.spec.footer is not None:
            # footer positioning
            pos = self.stylesheet.value('footer', 'position')
            hanchor = self.stylesheet.value('footer', 'hanchor')
            vanchor = self.stylesheet.value('footer', 'vanchor')
            x, y = [int(eval(e, {}, {'w':vw,'h':vh}))
                for e in pos if '_' not in e]
            x += vx
            y += vy

            # label
            # XXX should only need width for this label if centering
            l = pyglet.text.DocumentLabel(self.spec.footer, x, y, vw,
                anchor_x=hanchor, anchor_y=vanchor, multiline=True,
                dpi=int(scale*96), batch=self.batch)
            l.set_style('align', hanchor)
            self.decorations.append(l)

            # adjust automatic viewport restriction if the footer is at the bottom
            if not viewport and vanchor == 'bottom':
                x, y, w, h = self.limited_viewport
                footer_height = l.content_height + l.y
                if y < footer_height:
                    d = footer_height - y
                    y = footer_height
                    h -= d
                    self.limited_viewport = (x, y, w, h)

    def handle_resize(self):
        for decoration in self.decorations:
            decoration.delete()
        self.batch = None
        self.create()

    def draw(self):
        self.batch.draw()

class LayoutParser(object):
    '''Parse a layout spec and modify an existing Layout instance in place.
    '''
    def __init__(self, layout):
        self.layout = layout

    def parse(self, content):
        self.layout.quads = []
        self.layout.images = []
        for line in content.splitlines():
            if line[0] == ':': line = line[1:]
            directive, rest = line.split(':', 2)
            getattr(self, 'handle_%s'%directive.strip())(rest.strip())

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
        self.layout.images.append((fname, halign, valign))

    def handle_vgradient(self, gradient):
        w, h = cocos.director.director.window.get_size()
        s, e = [parse_color(color) for color in gradient.split(';')]
        c = s + e + e + s
        v = [0, h, 0, 0, w, 0, w, h]
        self.layout.quads.append((c, v))

    def handle_hgradient(self, gradient):
        w, h = cocos.director.director.window.get_size()
        s, e = [parse_color(color) for color in gradient.split(';')]
        c = s + e + e + s
        v = [0, h, w, h, w, 0, 0, 0]
        self.layout.quads.append((c, v))

    def handle_quad(self, quad):
        w, h = cocos.director.director.window.get_size()
        vars = dict(w=w, h=h)
        cur_color = None
        c = []
        v = []
        for entry in [e.strip() for e in quad.split(';')]:
            if entry[0] == 'C':
                cur_color = parse_color(entry[1:])
            elif entry[0] == 'V':
                if cur_color is None:
                    raise ValueError(
                        'invalid quad spec %r: needs color first'%quad)
                c.extend(cur_color)
                v.extend([int(eval(e, {}, vars))
                    for e in entry[1:].split(',') if '_' not in e])
        self.layout.quads.append((c, v))

