import pyglet
from pyglet import graphics
from pyglet.text import document, layout

from bruce import config
from bruce import page

class ReStructuredTextPage(page.Page):
    '''Displays some ReStructuredText (optionally from a file source).

    Requires docutils to be installed.
    '''
    config = (
        ('isfile', bool, False),
    )
    name = 'rst'
    def __init__(self, content, **kw):
        super(TextPage, self).__init__(content, **kw)

        if self.isfile:
            # content is a filename
            f = pyglet.resource.file(self.content)
            try:
                self.content = f.read()
            finally:
                f.close()

        content = '\n'.join(content)
        XXX more to do

        self.document = document.FormattedDocument(content)
        for s, e, attrs in styles:
            self.document.set_style(s, e, attrs)
        self.document.set_style(0, len(content), {'align': 'center'})

    def on_enter(self, vw, vh):
        # generate the document
        self.batch = graphics.Batch()
        self.layout = layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign='center'
        self.layout.y = vh//2

    def on_next(self):
        if self.exposed == len(self.blocks):
            return False
        s, e, color = self.blocks[self.exposed]
        self.document.set_style(s, e, {'color': color[:3] + (255,)})
        self.exposed += 1
        return True

    def on_previous(self):
        if self.exposed == 0:
            return False
        self.exposed -= 1
        s, e, color = self.blocks[self.exposed]
        self.document.set_style(s, e, {'color': color[:3] + (0,)})
        return True

    def on_leave(self):
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

config.add_section('text', {})
