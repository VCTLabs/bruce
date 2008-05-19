'''

Cocos:

- Page is actually a Scene.
- Content (current Page) is a Layer in that Scene.
- Decoration is another Layer.
- Presentation manages the Scenes.

'''


import pyglet

class Page(pyglet.event.EventDispatcher):
    def __init__(self, document, stylesheet, elements):
        self.document = document
        self.stylesheet = stylesheet
        self.elements = elements
        self.decoration = stylesheet['decoration']

    def layout(self, x, y, vw, vh):
        '''Invoked as part of on_enter handling.
        '''
        self.batch = pyglet.graphics.Batch()

        # render the text lines to our batch
        l = self._layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw, vh, multiline=True, batch=self.batch)

        # do alignment
        l.begin_update()
        l.valign = self.stylesheet['layout']['valign']
        if l.valign == 'center': l.y = y + vh//2
        elif l.valign == 'top': l.y = y + vh
        else: l.y = y
        l.end_update()

        # to support auto-resizing elements....
        # if you give the element a ref to the layout and total size, then it
        # can base its size off the difference.  you still need to do it in two
        # passes, but can avoid laying out everything again... just invalidate
        # the style of the element, which will push the rest of the content
        # down when pyglet notices its size has increased

    def cleanup(self):
        '''Invoked as part of on_leave handling.
        '''
        self._layout.delete()
        self._layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

    def update(self, dt):
        '''Invoked periodically with the time since the last
        update()
        '''
        pass

    def push_element_handlers(self, dispatcher):
        for element in self.elements:
            dispatcher.push_handlers(element)

    def pop_element_handlers(self, dispatcher):
        for element in self.elements:
            dispatcher.pop_handlers()

    def on_enter(self, viewport_width, viewport_height):
        '''Invoked when the page is put up on the screen of the given
        dimensions.
        '''
        self.decoration.on_enter(viewport_width, viewport_height)
        for element in self.elements:
            element.on_enter(viewport_width, viewport_height)
        self.layout(*self.decoration.get_viewport())

    def xon_resize(self, viewport_width, viewport_height):
        '''Invoked when the viewport has changed dimensions.

        Default behaviour is to clear the page and re-enter. Most pages
        will be able to handle this better.
        '''
        raise NotImplementedError('this used to call on_leave/on_enter but sucks')

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
        for element in self.elements:
            element.on_leave()
        self.cleanup()

    def do_draw(self):
        '''Invoked to render the page when active.

        Renders the decoration and then the implementation page's contents.
        '''
        self.decoration.draw()
        self.draw()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self._layout.view_x -= scroll_x
        self._layout.view_y += scroll_y * 32

Page.register_event_type('set_mouse_visible')
Page.register_event_type('set_fullscreen')

