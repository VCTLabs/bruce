
from pyglet.text.formats import structured

class ImageElement(structured.ImageElement):
    def __init__(self, image, width=None, height=None):

        flaw: can't have "fill space" ..... we need to know the dimension of this image to
        perform layout.

