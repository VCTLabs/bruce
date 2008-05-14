import os
import re

import pyglet
from pyglet.gl import glPushMatrix, glPopMatrix, glTranslatef

class Page(pyglet.event.EventDispatcher):
    def draw(self):
        '''Draw self - assume orthographic projection.
        '''
        raise NotImplementedError('implement draw() in subclass')

    def update(self, dt):
        '''Invoked periodically with the time since the last
        update()
        '''
        pass

    def on_enter(self, viewport_width, viewport_height):
        '''Invoked when the page is put up on the screen of the given
        dimensions.
        '''
        self.decoration.on_enter(viewport_width, viewport_height)
        self.layout(*self.decoration.get_viewport())

    def layout(self, viewport_x, viewport_y, viewport_width, viewport_height):
        '''Invoked as part of on_enter handling, must be provided by an
        implementation class.
        '''
        raise NotImplementedError('implement in subclass')

    def on_resize(self, viewport_width, viewport_height):
        '''Invoked when the viewport has changed dimensions.

        Default behaviour is to clear the page and re-enter. Most pages
        will be able to handle this better.
        '''
        self.on_leave()
        self.on_enter(viewport_width, viewport_height)

    def on_next(self):
        '''Invoked on the "next" event (cursor right or left mouse
        button). If the handler returns event.EVENT_HANDLED then
        the presentation does not leave this page.
        '''
        pass

    def on_previous(self):
        '''Invoked on the "previous" event (cursor left or right mouse
        button). If the handler returns event.EVENT_HANDLED then
        the presentation does not leave this page.
        '''
        pass

    def on_leave(self):
        '''Invoked when the page is removed from the screen.
        '''
        self.decoration.on_leave()
        self.cleanup()

    def cleanup(self):
        '''Invoked as part of on_leave handling, must be provided by an
        implementation class.
        '''
        raise NotImplementedError('implement in subclass')

    def do_draw(self):
        '''Invoked to render the page when active.

        Renders the decoration and then the implementation page's contents.
        '''
        self.decoration.draw()
        self.draw()

    def draw(self):
        '''Invoked as part of do_draw, must be provided by an
        implementation class.
        '''
        raise NotImplementedError('implement in subclass')


Page.register_event_type('set_mouse_visible')
Page.register_event_type('set_fullscreen')

