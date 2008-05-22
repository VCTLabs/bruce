
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
        width = width or image.width
        height = height or image.height

        super(ImageElement, self).__init__(image, width, height)

    def on_enter(self, vw, wh):
        self.image = pyglet.resource.image(self.uri)

    def on_leave(self):
        self.image = None

