import time
import pyglet
from pyglet.window import key, mouse

from bruce import resource

class Presentation(pyglet.event.EventDispatcher):

    def __init__(self, window, pages, start_page=0, show_timer=False,
            show_count=False):
        self.window = window
        self.window.set_mouse_visible(False)

        self.pages = pages
        if start_page < 0:
            start_page = start_page + len(pages)
        self.page_num = start_page
        self.num_pages = len(pages)

        if show_timer or show_count:
            self.batch = pyglet.graphics.Batch()
        else:
            self.batch = None
        self.show_timer = show_timer
        self.start_time = None
        y = 0
        if show_timer:
            self.timer_label = pyglet.text.Label('--:--',
                font_name='Courier New', font_size=24,
                color=(255, 255, 255, 150),
                halign='right', valign='bottom', batch=self.batch,
                x=self.window.width, y=0)
            y = self.timer_label.content_height

        self.show_count = show_count
        if show_count:
            self.count_label = pyglet.text.Label(
                '%d/%d'%(self.page_num+1, len(pages)),
                font_name='Courier New', font_size=24,
                color=(255, 255, 255, 150),
                halign='right', valign='bottom', batch=self.batch,
                x=self.window.width, y=y)

        self.player = pyglet.media.Player()

    def start_presentation(self):
        # set up the initial page
        self.page = self.pages[self.page_num]
        self.page.push_handlers(self)
        self.window.push_handlers(self.page)
        self.page.on_enter(self.window.width, self.window.height)
        self.window.set_caption('Presentation: Slide 1')
        pyglet.clock.schedule(self.page.update)
        self.dispatch_event('on_page_changed', self.page, self.page_num)

    def set_mouse_visible(self, visible):
        '''Invoked by events from pages.
        '''
        self.window.set_mouse_visible(visible)
        return pyglet.event.EVENT_HANDLED

    def set_fullscreen(self, fullscreen):
        '''Invoked by events from pages.
        '''
        self.window.set_fullscreen(fullscreen)
        return pyglet.event.EVENT_HANDLED

    __logo_spec = None
    __logo = None
    def on_draw(self):
        # set the clear color which is specified in 0-255 (and glClearColor
        # takes 0-1)
        pyglet.gl.glPushAttrib(pyglet.gl.GL_COLOR_BUFFER_BIT)
        clear_color = [v/255. for v in self.page.cfg['bgcolor']]
        pyglet.gl.glClearColor(*clear_color)

        self.window.clear()
        logo = self.page.cfg['logo']
        if logo != self.__logo_spec:
            valign = 'bottom'
            halign = 'right'
            if ';' in logo:
                fname, args = logo.split(';', 1)
            else:
                fname = logo
            self.__logo = pyglet.sprite.Sprite(resource.loader.image(fname))
            self.__logo.x = self.window.width - self.__logo.width
            self.__logo.y = 0

        if self.__logo and self.page.nofooter != True:
            self.__logo.draw()

        self.page.draw()
        if self.start_time is not None:
            t = time.time() - self.start_time
            self.timer_label.text = '%02d:%02d'%(t//60, t%60)
        if self.show_count:
            self.count_label.text = '%d/%d'%(self.page_num+1, len(self.pages))
        if self.batch is not None:
            self.batch.draw()

        pyglet.gl.glPopAttrib()

    def __move(self, dir):
        # start the timer if we're displaying one
        if self.show_timer and self.start_time is None:
            self.start_time = time.time()

        # determine the new page, with limits
        new = min(self.num_pages-1, max(0, self.page_num + dir))
        if new == self.page_num: return

        # leave the old page
        self.page_num = new
        self.page.on_leave()
        self.page.pop_handlers()
        self.window.remove_handlers(self.page)
        pyglet.clock.unschedule(self.page.update)

        # enter the new page
        self.page = self.pages[self.page_num]
        self.page.push_handlers(self)
        self.window.push_handlers(self.page)
        self.page.on_enter(self.window.width, self.window.height)
        pyglet.clock.schedule(self.page.update)

        self.window.set_caption("Presentation: Slide %d"%(self.page_num+1))

        # play the next page's sound (if any)
        # force skip of the rest of the current sound (if any)
        self.player.next()
        if self.page.sound:
            self.player.queue(self.page.sound)
            self.player.play()

        # let anyone listening know that the page has changed
        self.dispatch_event('on_page_changed', self.page, self.page_num)

    def __next(self):
        if not self.page.on_next():
            self.__move(1)

    def __previous(self):
        if not self.page.on_previous():
            self.__move(-1)

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

    def on_close(self):
        pyglet.app.exit()
        return pyglet.event.EVENT_HANDLED

    def on_key_press(self, pressed, modifiers):
        # move forward on space
        if pressed == key.SPACE:
            self.__next()

        # switch fullscreen/windowed on ctrl-F
        if pressed == key.F and modifiers & key.MOD_CTRL:
            self.window.set_fullscreen(not self.window.fullscreen)
            if not self.window.fullscreen:
                self.window.set_size(1024, 768)

    def on_text_motion(self, motion):
        if motion == key.MOTION_LEFT: self.__previous()
        elif motion == key.MOTION_RIGHT: self.__next()
        elif motion == key.MOTION_NEXT_PAGE: self.__move(5)
        elif motion == key.MOTION_PREVIOUS_PAGE: self.__move(-5)
        elif motion == key.MOTION_BEGINNING_OF_FILE: self.__move(self.num_pages)
        elif motion == key.MOTION_END_OF_FILE: self.__move(-self.num_pages)
        else: return pyglet.event.EVENT_UNHANDLED
        return pyglet.event.EVENT_HANDLED

    left_pressed = right_pressed = 0
    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.left_pressed = time.time()
            return pyglet.event.EVENT_HANDLED
        elif button == mouse.RIGHT:
            self.right_pressed = time.time()
            return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_UNHANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        # XXX need a better mouse click-or-drag detection method
        if button == mouse.LEFT and time.time() - self.left_pressed < .2:
            self.__next()
            return pyglet.event.EVENT_HANDLED
        elif button == mouse.RIGHT and time.time() - self.right_pressed < .2:
            self.__previous()
            return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_UNHANDLED

Presentation.register_event_type('on_page_changed')
Presentation.register_event_type('on_close')

