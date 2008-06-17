import time
import pyglet
import cocos
from cocos.director import director
from pyglet.window import key, mouse

from bruce import info_layer

class Presentation(pyglet.event.EventDispatcher):

    def __init__(self, pages, start_page, show_timer,
            show_count, desired_size):
        director.window.set_mouse_visible(False)

        self.pages = pages
        if start_page < 0:
            start_page = start_page + len(pages)
        self.page_num = start_page
        self.num_pages = len(pages)

        self.info_layer = None
        if show_timer or show_count:
            self.info_layer = info_layer.InfoLayer(show_timer, show_count, self.num_pages)
            self.push_handlers(self.info_layer)

        self.desired_size = desired_size

    def start_presentation(self):
        self.page = self.pages[self.page_num]
        self.page.desired_size = self.desired_size
        director.window.set_caption('Presentation: Slide 1')
        self.dispatch_event('on_page_changed', self.page, self.page_num)
        director.run(self.page)

    def _enter_page(self, page, forward=True):
        # set up the initial page
        old_page = self.page
        self.page = page
        page.desired_size = self.desired_size

        # enter the page
        if forward and page.transition is not None:
            page.transition(page)
        elif not forward and old_page.transition is not None:
            old_page.transition(page)
        else:
            director.replace(page)

        director.window.set_caption('Presentation: Slide 1')
        self.dispatch_event('on_page_changed', self.page, self.page_num)

    def on_resize(self, viewport_width, viewport_height):
        self.page.on_resize(viewport_width, viewport_height)

    def __move(self, dir):
        # determine the new page, with limits
        new = min(self.num_pages-1, max(0, self.page_num + dir))
        if new == self.page_num: return

        # leave the old page
        self.page_num = new

        # enter the new page
        self._enter_page(self.pages[self.page_num], dir>0)

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

    def on_text_motion(self, motion):
        if motion == key.MOTION_LEFT: self.__previous()
        elif motion == key.MOTION_RIGHT: self.__next()
        elif motion == key.MOTION_NEXT_PAGE: self.__move(5)
        elif motion == key.MOTION_PREVIOUS_PAGE: self.__move(-5)
        elif motion == key.MOTION_BEGINNING_OF_FILE: self.__move(-self.num_pages)
        elif motion == key.MOTION_END_OF_FILE: self.__move(self.num_pages)
        else: return pyglet.event.EVENT_UNHANDLED
        return pyglet.event.EVENT_HANDLED

    left_pressed = right_pressed = 0
    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.left_pressed = (time.time(), x, y)
            return pyglet.event.EVENT_HANDLED
        elif button == mouse.RIGHT:
            self.right_pressed = (time.time(), x, y)
            return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_UNHANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            st, sx, sy = self.left_pressed
            if time.time() - st < .2 and (abs(sx-x) + abs(sy-y) < 2):
                self.__next()
                return pyglet.event.EVENT_HANDLED
        elif button == mouse.RIGHT:
            st, sx, sy = self.right_pressed
            if time.time() - st < .2 and (abs(sx-x) + abs(sy-y) < 2):
                self.__previous()
                return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_UNHANDLED

Presentation.register_event_type('on_page_changed')
Presentation.register_event_type('on_close')

