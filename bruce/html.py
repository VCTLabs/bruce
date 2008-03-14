import pyglet
from pyglet import graphics
from pyglet.text import document, layout

from bruce import config
from bruce import page
from bruce import resource

class HTMLTextPage(page.ScrollableLayoutPage):
    '''Displays some HTML (with limits).

    '''
    config = (
        ('isfile', bool, False),
        ('color', tuple, (255, 255, 255, 255)),
    )
    name = 'html'
    def __init__(self, content, **kw):
        super(HTMLTextPage, self).__init__(content, **kw)

        if self.isfile:
            # content is a filename
            f = resource.loader.file(self.content)
            try:
                self.content = f.read()
            finally:
                f.close()

    def on_enter(self, vw, vh):
        super(HTMLTextPage, self).on_enter(vw, vh)
        self.document = pyglet.text.decode_html(self.content)
        self.document.set_style(0, len(self.document.text), {'color':
            self.cfg['color']})

        self.batch = graphics.Batch()
        self.layout = layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign='top'
        self.layout.y = vh

    def on_leave(self):
        self.document = None
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()


config.add_section('html', dict((k, v) for k, t, v in HTMLTextPage.config))

