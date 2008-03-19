import time
import pyglet

class Progress(pyglet.event.EventDispatcher):

    def __init__(self, window, presentation, source):
        self.window = window

        self.page_num = 0
        self.page_count = len(presentation.pages)

        self.source = source
        self.source_lines = source.splitlines()

        self.window.set_caption('Presentation: Slide 1')

        # make sure we close both windows on exit
        self._closing = False

        self.batch = pyglet.graphics.Batch()

        #source = 'aasdf\nasdfasdf'
        self.document = pyglet.text.document.FormattedDocument(source)
        self.document.set_style(0, len(source), {
            'color': (255, 255, 255, 255),
            'font_name': 'Courier New', 'font_size': 12,
        })

        vw, vh = window.width, window.height
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw, vh, multiline=True, batch=self.batch)
        self.layout.valign = 'top'
        self.layout.y = vh

        self.start_time = None
        y = 0
        self.timer_label = pyglet.text.Label('--:--',
            font_name='Courier New', font_size=24, bold=True,
            color=(255, 200, 200, 150),
            halign='right', valign='bottom', batch=self.batch,
            x=window.width, y=0)
        y = self.timer_label.content_height

        self.count_label = pyglet.text.Label(
            '%d/%d'%(self.page_num+1, self.page_count),
            font_name='Courier New', font_size=24, bold=True,
            color=(255, 200, 200, 150),
            halign='right', valign='bottom', batch=self.batch,
            x=window.width, y=y)

        pyglet.clock.schedule(self.update)

    start_pos = end_pos = None
    def on_page_changed(self, page, page_num):
        if self.start_pos is not None:
            self.document.set_style(self.start_pos, self.end_pos, {
                'color': (255, 255, 255, 255),
            })

        if self.start_time is None:
            self.start_time = time.time()
        self.page_num = page_num
        self.count_label.text = '%d/%d'%(self.page_num+1, self.page_count)
        self.window.set_caption('Presentation: Slide %d'%(self.page_num+1,))

        # scroll to ensure the top of the page's source is visible
        self.start_pos = page.start_pos #self.layout.get_position_from_line(page.start_line)
        self.end_pos = page.end_pos #self.layout.get_position_from_line(page.end_line)
        start_line = self.layout.get_line_from_position(self.start_pos)
        if start_line:
            self.layout.view_y = self.layout.lines[start_line-1].y
        else:
            self.layout.view_y = 0

        print '*'*75
        print start_line
        print `self.source[self.start_pos:self.end_pos]`

        self.document.set_style(self.start_pos, self.end_pos, {
            'color': (255, 0, 0, 255),
        })

    def update(self, dt):
        if self.start_time is not None:
            t = time.time() - self.start_time
            t = '%02d:%02d'%(t//60, t%60)
            if t != self.timer_label.text:
                self.timer_label.text = t

    # XXX on_resize?

    def on_draw(self):
        self.window.clear()
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


    # pass these back to the presentation if it's listening
    def on_key_press(self, pressed, modifiers):
        if self.dispatch_event('on_key_press', pressed, modifiers):
            return pyglet.event.EVENT_HANDLED
        return pressed != pyglet.window.key.ESCAPE

    def on_text_motion(self, motion):
        return self.dispatch_event('on_text_motion', motion)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_press', x, y, button,
            modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_release', x, y, button,
            modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # XXX pass to presentation if done over that
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 16

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # XXX pass to presentation if done over that
        self.layout.view_y -= dy

    def on_close(self):
        pyglet.app.exit()
        return pyglet.event.EVENT_HANDLED

Progress.register_event_type('on_key_press')
Progress.register_event_type('on_text_motion')
Progress.register_event_type('on_mouse_press')
Progress.register_event_type('on_mouse_release')

