
import pyglet
from pyglet.text.formats import structured

from cocos.director import director

def calculate_dimensions(width, height, image):
    # handle width and height, retaining aspect if only one is specified
    if height is not None and width is None:
        scale = height / float(image.height)
        width = int(scale * image.width)
    elif width is not None:
        scale = width / float(image.width)
        height = int(scale * image.height)
    return width or image.width, height or image.height

class ImageElement(structured.ImageElement):
    def __init__(self, uri, width=None, height=None, fit=False):
        self.uri = uri
        image = pyglet.resource.image(uri)

        if fit:
            # XXX actually use this somehow some day
            # go for best fit
            width, height = map(float, director.get_window_size())
            scale = min(width / image.width, height / image.height)
            width = int(image.width * scale)
            height = int(image.height * scale)

        self.width_spec = width
        self.height_spec = height
        self.scale = 1.0
        self.opacity = 255

        self.width, self.height = calculate_dimensions(width, height, image)

        super(ImageElement, self).__init__(image, self.width, self.height)

    def place(self, layout, x, y):

        # override to use c4B and blending
        group = pyglet.sprite.SpriteGroup(self.image.texture,
            pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA,
            layout.top_group)

        x1 = int(x)
        y1 = int(y + self.descent)
        x2 = int(x + self.width)
        y2 = int(y + self.height + self.descent)
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('c4B', [255, 255, 255, self.opacity] * 4),
            ('t3f', self.image.tex_coords))
        self.vertex_lists[layout] = vertex_list

    def remove(self, layout):
        self.vertex_lists[layout].delete()
        del self.vertex_lists[layout]

    def set_opacity(self, layout, opacity):
        self.opacity = int(opacity)
        self.vertex_lists[layout].colors[:] = [255, 255, 255, self.opacity]*4

    def set_scale(self, scale):
        if self.scale == scale:
            return

        width, height = calculate_dimensions(self.width_spec, self.height_spec, self.image)
        self.width = int(width*scale)
        self.height = int(height*scale)

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

