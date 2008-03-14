import os

import pyglet
from pyglet import graphics
from pyglet import text
from pyglet.text import document, layout

from bruce import config
from bruce import page
from bruce import resource

class CodePage(page.PageWithTitle, page.ScrollableLayoutPage):
    '''Displays some code from a file.
    '''
    config = (
        ('title', str, ''),
        ('title.font_name', str, 'Arial'),
        ('title.font_size', float, 64),
        ('title.color', tuple, (200, 255, 255, 255)),
        # fits 80 columns across 1024 pixels
        ('code.font_name', str, 'Courier New'),
        ('code.font_size', float, 20),
        ('code.color', tuple, (200, 255, 200, 255)),
    )
    name = 'code'

    def __init__(self, content, **kw):
        super(CodePage, self).__init__(content, **kw)

        # load the file content
        f = resource.loader.file(self.content.strip())
        try:
            self.file_content = f.read().decode(self.cfg['charset'])
        finally:
            f.close()

        # XXX put up a background too

    label = None
    def on_enter(self, vw, vh):
        super(CodePage, self).on_enter(vw, vh)

        # format the code
        self.document = document.FormattedDocument(self.file_content)
        self.document.set_style(0, len(self.file_content), {
            'font_name': self.cfg['code.font_name'],
            'font_size': self.cfg['code.font_size'],
            'color': self.cfg['code.color'],
        })

        self.batch = graphics.Batch()

        self.generate_title()

        # generate the document
        self.layout = layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign = 'top'

        # position all the elements
        self.on_resize(vw, vh)

    def on_resize(self, vw, vh):
        self.viewport_width, self.viewport_height = vw, vh

        # position the title and adjust the available viewport height
        if self.title_label:
            self.title_label.x = vw//2
            self.title_label.y = vh = vh - self.title_label.content_height

        # position the code layout
        self.layout.begin_update()
        self.layout.x = 2
        self.layout.width = vw - 4
        self.layout.height = vh
        self.layout.y = vh
        self.layout.end_update()

    def on_leave(self):
        self.document = None
        self.title_label = None
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

config.add_section('code', dict((k, v) for k, t, v in CodePage.config))

