import time
import pyglet
from pyglet.gl import *

class Progress(pyglet.event.EventDispatcher):

    def __init__(self, window, presentation, source):
        self.window = window

        pyglet.gl.glClearColor(1., 1., 1., 1.)

        self.presentation = presentation
        self.page_num = 0
        self.page_count = len(presentation.pages)

        self.source = source
        self.source_lines = source.splitlines()

        self.window.set_caption('Presentation: Slide 1')

        # make sure we close both windows on exit
        self._closing = False

        self.batch = pyglet.graphics.Batch()

        # figure font scale
        sx = window.width / 1280.
        sy = window.height / 480.
        scale = min(sx, sy)

        self.document = pyglet.text.document.FormattedDocument(source)
        self.document.set_style(0, len(source), {
            'color': (0, 0, 0, 255),
            'background_color': (255, 255, 255, 255),
            'font_name': 'Courier New', 'font_size': 12*scale,
        })

        vw, vh = window.width, window.height
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw//2 - 4, vh, multiline=True, batch=self.batch)
        self.layout.valign = 'top'
        self.layout.x = 2 + vw//2
        self.layout.y = vh

        self.caret = pyglet.text.caret.Caret(self.layout)
        self.caret.on_activate()

        self.start_time = None
        y = 0
        self.timer_label = pyglet.text.Label('--:--',
            font_name='Courier New', font_size=24*scale, bold=True,
            color=(255, 200, 200, 150),
            halign='right', valign='bottom', batch=self.batch,
            x=window.width, y=0)
        y = self.timer_label.content_height

        self.count_label = pyglet.text.Label(
            '%d/%d'%(self.page_num+1, self.page_count),
            font_name='Courier New', font_size=24*scale, bold=True,
            color=(255, 200, 200, 150),
            halign='right', valign='bottom', batch=self.batch,
            x=window.width, y=y)

        pyglet.clock.schedule(self.update)

    start_pos = end_pos = None
    def on_page_changed(self, page, page_num):
        if self.start_pos is not None:
            self.document.set_style(self.start_pos, self.end_pos, {
                'color': (0, 0, 0, 255),
                'background_color': (255, 255, 255, 255),
            })

        if self.start_time is None:
            self.start_time = time.time()
        self.page_num = page_num
        self.count_label.text = '%d/%d'%(self.page_num+1, self.page_count)
        self.window.set_caption('Presentation: Slide %d'%(self.page_num+1,))

        # scroll to ensure the top of the page's source is visible
        self.start_pos = page.start_pos
        self.end_pos = page.end_pos
        #start_line = self.layout.get_line_from_position(self.start_pos)
        #if start_line:
            #self.layout.view_y = self.layout.lines[start_line-1].y
        #else:
            #self.layout.view_y = 0
        self.caret.position = page.start_pos

        # colour the currently-active section of the source
        self.document.set_style(self.start_pos, self.end_pos, {
            'background_color': (255, 255, 100, 255),
        })

    def update(self, dt):
        if self.start_time is not None:
            t = time.time() - self.start_time
            t = '%02d:%02d'%(t//60, t%60)
            if t != self.timer_label.text:
                self.timer_label.text = t

    # XXX on_resize?

    def on_draw(self):
        vw = float(self.window.width//2)
        vh = float(self.window.height)
        sx = vw / self.presentation.window.width
        sy = vh / self.presentation.window.height
        scale = min(sx, sy)

        glPushMatrix()
        glScalef(scale, scale, 1)
        self.presentation.on_draw()
        glPopMatrix()

        glBegin(GL_QUADS)
        glColor4f(1, 1, 1, 1)
        glVertex2f(vw, 0)
        glVertex2f(vw, vh)
        glVertex2f(self.window.width, vh)
        glVertex2f(self.window.width, 0)
        glEnd()
        self.batch.draw()

    def dispatch_event(self, event_type, *args):
        '''Overridden so it doesn't invoke the method on self and cause a loop
        '''
        assert event_type in self.event_types

        # Search handler stack for matching event handlers
        for frame in list(self._event_stack):
            handler = frame.get(event_type, None)
            if handler:
                try:
                    if handler(*args):
                        return
                except TypeError:
                    self._raise_dispatch_exception(event_type, args, handler)

    # XXX pass these to the presentation?
    def on_text(self, symbol):
        return self.caret.on_text(symbol)

    def on_text_motion(self, motion):
        return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        return self.caret.on_text_motion_select(motion)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        return self.caret.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_press', x, y, button,
            modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_release', x, y, button,
            modifiers)

    def on_close(self):
        pyglet.app.exit()
        return pyglet.event.EVENT_HANDLED

Progress.register_event_type('on_key_press')
Progress.register_event_type('on_text_motion')
Progress.register_event_type('on_mouse_press')
Progress.register_event_type('on_mouse_release')

