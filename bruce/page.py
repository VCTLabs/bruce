import pyglet
import cocos
from cocos.director import director

class Page(cocos.scene.Scene):
    def __init__(self, document, stylesheet, layout, elements, docnode):
        cocos.scene.Scene.__init__(self)
        pyglet.event.EventDispatcher.__init__(self)
        self.layout = layout
        self.add(self.layout, z=-.5)
        self.content = PageContent(document, stylesheet, elements)
        self.add(self.content, z=0)
        self.docnode = docnode
        self.transition = stylesheet.get_transition()

        viewport_width, viewport_height = director.get_window_size()

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

    def print_source(self):
        for child in self.docnode.children:
            print str(child)

    def get_viewport(self):
        return self.layout.get_viewport()


class PageContent(cocos.layer.Layer):
    is_event_handler = True
    def __init__(self, document, stylesheet, elements):
        self.document = document
        self.stylesheet = stylesheet
        self.elements = elements
        super(PageContent, self).__init__()

    # XXX Cocos doesn't invoke a push_all_handlers for some reason
    # so I do it manually in on_enter
    def _push_all_handlers(self):
#        director.window.push_handlers(self)
        for element in self.elements:
            director.window.push_handlers(element)

    def _remove_all_handlers(self):
        for element in self.elements:
            director.window.pop_handlers()
#        director.window.pop_handlers()

    def update(self, dt):
        '''Invoked periodically with the time since the last
        update()
        '''
        pass


    def on_enter(self):
        '''Invoked when the page is put up on the screen of the given
        dimensions.
        '''
        super(PageContent, self).on_enter()
        self._push_all_handlers()

        x, y, vw, vh = self.parent.get_viewport()

        for element in self.elements:
            element.on_enter(vw, vh)

        self.batch = pyglet.graphics.Batch()

        # render the text lines to our batch
        l = self.text_layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw, vh,
            multiline=True, batch=self.batch)

        l.begin_update()
        valign = self.stylesheet['layout']['valign']
        if valign == 'center': l.y = y + vh//2
        elif valign == 'top': l.y = y + vh
        else: l.y = y
        l.anchor_y=valign
        l.content_valign=valign
        l.end_update()

        # XXX to support auto-resizing elements....
        # if you give the element a ref to the layout and total size, then it
        # can base its size off the difference.  you still need to do it in two
        # passes, but can avoid laying out everything again... just invalidate
        # the style of the element, which will push the rest of the content
        # down when pyglet notices its size has increased


    def on_resize(self, w, h):
        self.parent.layout.on_resize(w, h)
        x, y, vw, vh = self.parent.get_viewport()
        l = self.text_layout
        l.begin_update()
        l.x = x
        if l.anchor_y == 'center': l.y = y + vh//2
        elif l.anchor_y == 'top': l.y = y + vh
        else: l.y = y
        l.width = vw
        l.height = vh
        l.end_update()

    def on_exit(self):
        '''Invoked when the page is removed from the screen.
        '''
        self._remove_all_handlers()
        super(PageContent, self).on_exit()
        if self._cb_hide_mouse_scheduled:
            self.cb_hide_mouse(0)
        for element in self.elements:
            element.on_exit()
        self.text_layout.delete()
        self.text_layout = None
        self.batch = None

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.text_layout.view_x -= scroll_x
        self.text_layout.view_y += scroll_y * 32

    def on_mouse_motion(self, x, y, dx, dy):
        director.window.set_mouse_visible(True)
        if not self._cb_hide_mouse_scheduled:
            pyglet.clock.schedule_once(self.cb_hide_mouse, 2)
            self._cb_hide_mouse_scheduled = True

    _cb_hide_mouse_scheduled = False
    def cb_hide_mouse(self, dt):
        self._cb_hide_mouse_scheduled = False
        director.window.set_mouse_visible(False)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.text_layout.view_y -= dy

    def draw(self):
        self.batch.draw()

