import os

import pyglet
from pyglet import graphics
from pyglet import text
from pyglet import sprite
from pyglet import gl

from bruce import config
from bruce import page
from bruce import resource

# XXX this doesn't appear to be working... I still see an artifact on the very
# edge of a blown-up image
class ClampTextureImageGroup(graphics.Group):
    def set_state(self):
        gl.glPushAttrib(gl.GL_TEXTURE_BIT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
            gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
            gl.GL_CLAMP_TO_EDGE)

    def unset_state(self):
        gl.glPopAttrib()

class ImagePage(page.PageWithTitle, page.Page):
    config = (
        ('zoom', bool, False),
        ('title', unicode, ''),
        ('caption', unicode, ''),
        ('text.font_name', str, 'Arial'),
        ('text.font_size', float, 64),
        ('text.color', tuple, (255, 255, 255, 255)),
        ('title.font_name', str, 'Arial'),
        ('title.font_size', float, 64),
        ('title.color', tuple, (200, 255, 255, 255)),
    )
    name = 'image'

    @classmethod
    def as_html(cls, content, **kw):
        inst = cls(content, **kw)
        path = os.path.join(config.get('directory'), inst.content)
        l = []
        if inst.cfg['title']:
            l.append('<b>%s</b>'%inst.cfg['title'])
        l.append('<img height="100" src="%s">'%path)
        if inst.cfg['caption']:
            l.append(inst.cfg['caption'])
        return '<br>'.join(l)

    caption_label = None
    def on_enter(self, vw, vh):
        super(ImagePage, self).on_enter(vw, vh)

        self.batch = graphics.Batch()

        # load the image
        path = self.content.strip()
        if os.path.exists(path):
            im = pyglet.image.load(path)
        else:
            im = resource.loader.image(path)
        self.image_width = im.width
        self.image_height = im.height
        im.anchor_x = im.width//2
        im.anchor_y = im.height//2
        self.image = sprite.Sprite(im, 0, 0, group=ClampTextureImageGroup(),
            batch=self.batch)

        # if we have a title then generate it
        self.generate_title()

        # if we have a caption then generate it
        if self.cfg['caption']:
            self.caption_label = text.Label(self.cfg['caption'],
                font_name=self.cfg['text.font_name'],
                font_size=self.cfg['text.font_size'],
                color=self.cfg['text.color'],
                halign='center', valign='bottom', batch=self.batch)

        # position all the elements
        self.on_resize(vw, vh)

    def on_resize(self, vw, vh):
        self.viewport_width, self.viewport_height = vw, vh

        # position the labels and adjust the available viewport height
        if self.title_label:
            self.title_label.x = vw//2
            self.title_label.y = vh = vh - self.title_label.content_height

        yoffset = 0
        if self.caption_label:
            self.caption_label.x = vw//2
            self.caption_label.y = 0
            vh -= self.caption_label.content_height
            # shift up to avoid the caption
            yoffset += self.caption_label.content_height

        # make width and height even to avoid placing the image on a
        # half-pixel bounday when centered
        vw -= vw %2
        vh -= vh %2

        # determine whether we're scaling
        w, h = self.image_width, self.image_height
        if self.zoom or w > vw or h > vh:
            self.image.scale = min(vw / float(w), vh / float(h))

        # and center the image
        self.image.position = (vw//2, yoffset + vh//2)

    def on_leave(self):
        self.image = None
        self.batch = None
        self.title_label = None
        self.caption_label = None

    def draw(self):
        self.batch.draw()

config.add_section('image', ImagePage.config)

