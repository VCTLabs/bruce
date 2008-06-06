import time
import pyglet
import cocos
from cocos.director import director
from cocos.scenes import transitions
from pyglet.window import key, mouse

from bruce import info_layer

class Presentation(pyglet.event.EventDispatcher):

    def __init__(self, pages, start_page=0, show_timer=False,
            show_count=False):
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

        self.player = pyglet.media.Player()

    def start_presentation(self):
        self._enter_page(self.pages[self.page_num], first=True)

    def _enter_page(self, page, first=False):
        # set up the initial page
        self.page = page

        # enter the page
        if first:
            director.run(page)
        else:
            #director.replace(transitions.FadeTRTransition(page, duration=1))
            #director.replace(transitions.FadeTransition(page, duration=1))
            #director.replace(transitions.ShrinkGrowTransition(page, duration=1))
            director.replace(transitions.FlipY3DTransition(page, duration=1))
            #director.replace(page)

        director.window.set_caption('Presentation: Slide 1')
        self.dispatch_event('on_page_changed', self.page, self.page_num)

        '''
        # play the next page's sound (if any)
        # force skip of the rest of the current sound (if any)
        self.player.next()
        if self.page.cfg['sound']:
            self.player.queue(self.page.cfg['sound'])
            self.player.play()
        '''

    def on_resize(self, viewport_width, viewport_height):
        # XXX set DPI scaled according to viewport change.
        pass

    def __move(self, dir):

        # determine the new page, with limits
        new = min(self.num_pages-1, max(0, self.page_num + dir))
        if new == self.page_num: return

        # leave the old page
        self.page_num = new

        # enter the new page
        self._enter_page(self.pages[self.page_num])

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
        # XXX maybe keep this depending on how well Cocos' fullscreen switch works
        if 0: #pressed == key.F and modifiers & key.MOD_CTRL:
            if not self.window.fullscreen:
                self.window._restore_size = (
                    self.window.width, self.window.height)
            self.window.set_fullscreen(not self.window.fullscreen)
            if not self.window.fullscreen:
                self.window.set_size(*self.window._restore_size)

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

