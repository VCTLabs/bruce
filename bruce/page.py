import pyglet
import cocos
from cocos.actions import FadeIn, FadeOut
from cocos.director import director

class Page(cocos.scene.Scene):
    def __init__(self, document, stylesheet, elements, docnode,
            expose_text_runs):
        cocos.scene.Scene.__init__(self)
        pyglet.event.EventDispatcher.__init__(self)

        self.document = document
        self.stylesheet = stylesheet

        # background decoration / title / footer
        self.layout = stylesheet['layout'].layer(stylesheet)
        self.add(self.layout, z=-.5)

        # actual page content
        self.content = PageContent(document, stylesheet, elements,
            expose_text_runs)
        self.add(self.content, z=0)

        self.docnode = docnode
        self.transition = stylesheet.get_transition()

        viewport_width, viewport_height = director.get_window_size()

    def on_next(self):
        '''Invoked on the "next" event (cursor right or left mouse
        button). If the handler returns event.EVENT_HANDLED then
        the presentation does not leave this page.
        '''
        # XXX consider that this is suboptimal
        return self.content.on_next()

    def on_previous(self):
        '''Invoked on the "previous" event (cursor left or right mouse
        button). If the handler returns event.EVENT_HANDLED then
        the presentation does not leave this page.
        '''
        # XXX consider that this is suboptimal
        return self.content.on_previous()

    def print_source(self):
        for child in self.docnode.children:
            print str(child)

    def get_viewport(self):
        return self.layout.get_viewport()

    def get_scale(self):
        '''Determine how to scale the original resolution to the current
        physical display. Passed in the new physical resolution (most
        likely from on_resize).
        '''
        w, h = director.window.get_size()
        ow, oh = self.desired_size
        sx = w / float(ow)
        sy = h / float(oh)
        return min(sx, sy)

    def on_resize(self, w, h):
        # figure the scaling factor
        scale = self.get_scale()

        # right, now resize bits
        self.layout.handle_resize()
        x, y, vw, vh = self.get_viewport()
        self.content.handle_resize(x, y, vw, vh, scale)

class FadeSection(object):
    def __init__(self, layout, document, section):
        self.layout = layout
        self.document = document
        self.section = section

    def set_opacity(self, opacity):
        v = opacity/255.
        opacity = int(opacity)

        self.layout.begin_update()

        for element in self.section['elements']:
            element.set_opacity(self.layout, opacity)

        for s, e, color in self.section['runs']:
            color = color[:3] + (int(v * color[3]),)
            self.document.set_style(s, e, dict(color=color))

        self.layout.end_update()

    opacity = property(lambda s:s._opacity, set_opacity) 

class PageContent(cocos.layer.Layer):
    is_event_handler = True
    def __init__(self, document, stylesheet, elements, expose_text_runs):
        self.document = document
        self.stylesheet = stylesheet
        self.elements = elements
        self.expose_text_runs = expose_text_runs
        super(PageContent, self).__init__()

    def update(self, dt):
        '''Invoked periodically with the time since the last
        update()

        XXX except not
        '''
        pass

    def on_enter(self):
        '''Invoked when the page is put up on the screen of the given
        dimensions.
        '''
        super(PageContent, self).on_enter()

        # create the layout
        self.batch = pyglet.graphics.Batch()
        x, y, vw, vh = self.parent.get_viewport()
        self.create_layout(x, y, vw, vh, self.parent.get_scale())

        # set all top exposable sections to transparent
        self.text_layout.begin_update()
        for section in self.expose_text_runs:
            section['on'] = False
            for element in section['elements']:
                element.set_opacity(self.text_layout, 0)
            for s, e, color in section['runs']:
                color = color[:3] + (0,)
                self.document.set_style(s, e, dict(color=color))
        self.text_layout.end_update()

    def on_next(self):
        for section in self.expose_text_runs:
            if section['on']: continue
            section['on'] = True
            if section['style'] == 'fade':
                self.do(FadeIn(.5), FadeSection(self.text_layout, self.document, section))
            else:
                self.text_layout.begin_update()
                for element in section['elements']:
                    element.set_opacity(self.text_layout, 255)
                for s, e, color in section['runs']:
                    self.document.set_style(s, e, dict(color=color))
                self.text_layout.end_update()
            return pyglet.event.EVENT_HANDLED

    def on_previous(self):
        for section in reversed(self.expose_text_runs):
            if not section['on']: continue
            section['on'] = False
            if section['style'] == 'fade':
                self.do(FadeOut(.5), FadeSection(self.text_layout, self.document, section))
            else:
                self.text_layout.begin_update()
                for element in section['elements']:
                    element.set_opacity(self.text_layout, 0)
                for s, e, color in section['runs']:
                    color = color[:3] + (0,)
                    self.document.set_style(s, e, dict(color=color))
                self.text_layout.end_update()
            return pyglet.event.EVENT_HANDLED

    _current_dimensions = None
    def create_layout(self, x, y, vw, vh, scale):
        # remember these dimensions for later so we don't
        # re-calc on a NOOP resize
        self._current_dimensions = (x, y, vw, vh, scale)

        # set scale factor on inline elements
        for element in self.elements:
            element.set_scale(scale)

        # render the text lines to our batch
        l = self.text_layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw, vh, dpi=int(scale*96), multiline=True,
            batch=self.batch)

        # set dimensions & alignment in one go
        l.begin_update()
        valign = self.stylesheet['layout']['valign']
        if valign == 'center': l.y = y + vh//2
        elif valign == 'top': l.y = y + vh
        else: l.y = y
        l.x = x
        l.anchor_y=valign
        l.content_valign=valign
        l.end_update()

        # XXX to support auto-resizing elements....
        # if you give the element a ref to the layout and total size, then it
        # can base its size off the difference.  you still need to do it in two
        # passes, but can avoid laying out everything again... just invalidate
        # the style of the element, which will push the rest of the content
        # down when pyglet notices its size has increased

    def handle_resize(self, x, y, vw, vh, scale):
        # detect no change
        if self._current_dimensions == (x, y, vw, vh, scale):
            return

        # force re-layout
        self.text_layout.delete()
        self.create_layout(x, y, vw, vh, scale)

    def on_exit(self):
        '''Invoked when the page is removed from the screen.
        '''
        # now do me (this will remove my event handlers)
        super(PageContent, self).on_exit()

        # disable the mouse hiding
        if self._cb_hide_mouse_scheduled:
            self.cb_hide_mouse(0)

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

