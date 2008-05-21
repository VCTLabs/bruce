
import pyglet
from pyglet.text.formats import structured

class ImageElement(structured.ImageElement):
    def __init__(self, uri, width=None, height=None):
        self.uri = uri
        image = pyglet.resource.image(uri)

        # XXX allow image to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        if height is not None:
            if width is None:
                scale = height / float(image.height)
                width = int(scale * image.width)
        elif width is not None:
            scale = width / float(image.width)
            height = int(scale * image.height)
        self.width = width or image.width
        self.height = height or image.height

        self.vertex_lists = {}

        anchor_y = self.height / image.height * image.anchor_y
        ascent = max(0, self.height - anchor_y)
        descent = min(0, -anchor_y)
        super(structured.ImageElement, self).__init__(ascent, descent, self.width)

    def on_enter(self, vw, wh):
        self.image = pyglet.resource.image(self.uri)

    def on_leave(self):
        self.image = None

