
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

        width, height = calculate_dimensions(width, height, image)

        super(ImageElement, self).__init__(image, width, height)

    def set_scale(self, scale):
        width, height = calculate_dimensions(self.width_spec, self.height_spec, self.image)
        self.width = int(width*scale)
        self.height = int(height*scale)

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

    def on_enter(self, viewport_width, viewport_height):
        pass

    def on_exit(self):
        pass
