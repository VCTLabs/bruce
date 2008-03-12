import os

from cgi import escape as html_quote

import pyglet

from bruce import config

def decode_content(page, content):
    charset = page.cfg['charset']
    if charset.lower() == 'ascii':
        # convert escaped unicode into unicode
        if '\u' in content or '\U' in content:
            return content.decode('unicode_escape')
        return content
    return content.decode(charset)

class Page(pyglet.event.EventDispatcher):
    nofooter = False

    default_config = (
        ('nofooter', bool,  False),
        #('auto',     float, None),
        ('sound',    str,   None),
        ('logo',     str,   None),
        ('charset',  str,   'ascii'),
        ('bgcolor',  tuple, (0, 0, 0, 255)),
    )
    config = ()

    def __init__(self, content, source=[], **kw):
        '''Initialise the page given the content and config.
        '''
        self.source = '\n'.join(source)

        for name, type, default in self.default_config + self.config:
            if name in kw:
                if type is tuple:
                    val = tuple(int(v.strip()) for v in kw[name].split(','))
                    if len(val) < 4:
                        val += (255,)
                    kw[name] = val
                else:
                    kw[name] = type(kw[name])

        self.cfg = config.get_section(self.name)
        self.cfg.update(kw)

        for name, type, default in self.default_config + self.config:
            if name in kw:
                setattr(self, name, kw[name])
                del kw[name]
            else:
                setattr(self, name, default)

        if kw:
            raise ValueError('unknown flags %r'%(kw,))

        if self.sound:
            if os.path.exists(self.sound):
                self.sound = pyglet.media.load(self.sound, streaming=False)
            else:
                # avoid circular import problem
                from bruce import resource
                self.sound = resource.loader.media(self.sound,
                    streaming=False)

        self.content = decode_content(self, content)

    def font_size(self, name):
        base = self.cfg[name]
        sx = self.viewport_width / 1024.
        sy = self.viewport_height / 768.
        scale = min(sx, sy)
        return base * scale

    @classmethod
    def as_page(cls, content, **kw):
        return cls(content, **kw)

    @classmethod
    def as_html(cls, content, **kw):
        '''Invoked to generate the HTML version of the presentation.
        '''
        if not content:
            return ''
        content = decode_content(cls, content)
        return '<pre>%s</pre>'%html_quote(content)

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
        self.viewport_width, self.viewport_height = viewport_width, viewport_height

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
        pass

Page.register_event_type('set_mouse_visible')
Page.register_event_type('set_fullscreen')



class ScrollableLayoutPage(Page):
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 16

    def on_resize(self, vw, vh):
        # all of the ScrollableLayoutPage pages have a layout and optionally a
        # label at the top
        if self.label:
            self.label.x = vw // 2
            self.label.y = vw // 2
            vh -= self.label.content_height
        self.layout.width = vw
        self.layout.height = vh
        self.layout.y = vh

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        #self.layout.view_x += dx
        self.layout.view_y -= dy

