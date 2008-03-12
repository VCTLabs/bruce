import pyglet
from pyglet import graphics
from pyglet.text import document, layout

from bruce import config
from bruce import page

bullets = u'\u25cf\u25cb\u25a1'*3 # (just in case)

class Effect(object):
    def __init__(self, page, s, e, duration=1, **kw):
        self.page, self.s, self.e = page, s, e
        if (s, e) in page.effects:
            page.effects[s, e].cancel()
        page.effects[s, e] = self
        for k in kw: setattr(self, k, kw[k])
        self.t = 0
        self.duration = duration
        pyglet.clock.schedule(self)

    def cancel(self):
        pyglet.clock.unschedule(self)
        del self.page.effects[self.s, self.e]

    def __call__(self, dt):
        self.t += dt
        if self.t > self.duration:
            self.effect(1)
            self.cancel()
        else:
            self.effect(self.t / self.duration)

class FadeIn(Effect):
    def effect(self, n):
        rgba = self.rgb + (int(255 * n),)
        self.page.document.set_style(self.s, self.e, dict(color=rgba))

class FadeOut(Effect):
    def effect(self, n):
        rgba = self.rgb + (int(255 * (1-n)),)
        self.page.document.set_style(self.s, self.e, dict(color=rgba))

class TextPage(page.Page):
    config = (
        ('valign', str, 'center'),
        ('halign', str, 'center'),
        ('text.font_name', str, 'Arial'),
        ('text.font_size', float, 64),
        ('text.color', tuple, (255, 255, 255, 255)),
        ('title.font_name', str, 'Arial'),
        ('title.font_size', float, 64),
        ('title.color', tuple, (255, 255, 100, 255)),
        ('code.font_name', str, 'Courier New'),
        ('code.font_size', float, 64),
        ('code.color', tuple, (200, 200, 200, 255)),
    )
    name = 'text'

    def __init__(self, *args, **kw):
        super(TextPage, self).__init__(*args, **kw)
        self.effects = {}
        # XXX move this to config
        assert self.valign in 'center bottom top'.split()
        assert self.halign in 'center left right'.split()

    def on_enter(self, vw, vh):
        super(TextPage, self).on_enter(vw, vh)

        content = []
        styles = []
        n = 0
        self.blocks = []
        self.exposed = 0
        for line in self.content.splitlines():
            if line.startswith('#'): continue

            # set up style defaults
            style = dict(font_name=self.cfg['text.font_name'],
                font_size=self.font_size('text.font_size'),
                color=self.cfg['text.color'])

            # handle styling prefix
            hide = False
            bullet = 0
            while line and line[0] in '|[].<>=:*-/\\':
                ch, line = line[0], line[1:]
                if ch == "\\":
                    break
                elif ch == "-":
                    # XXX start and end for *block* not single line
                    hide = True
                elif ch == "<":
                    style['font_size'] *= 0.75
                elif ch == ">":
                    style['font_size'] *= 1.33
                elif ch == "/":
                    style['italic'] = True
                elif ch == "*":
                    style['bold'] = True
                elif ch == "[":
                    style['align'] = 'left'
                elif ch == "|":
                    style['align'] = 'center'
                elif ch == "]":
                    style['align'] = 'right'
                elif ch == ".":
                    bullet += 1
                    style['font_size'] *= 0.75
                elif ch == '=':
                    style['font_name'] = self.cfg['title.font_name']
                    style['font_size'] = self.font_size('title.font_size')
                    style['color'] = self.cfg['title.color']
                elif ch == ':':
                    style['font_name'] = self.cfg['code.font_name']
                    style['font_size'] = self.font_size('code.font_size')
                    style['color'] = self.cfg['code.color']
            if bullet:
                # add a circle to the start of line
                style['margin_left'] = 50*bullet
                line = bullets[bullet-1] + ' ' + line
            if hide:
                color = style['color']
                self.blocks.append((n, n+len(line), color))
                style['color'] = color[:3] + (0,)
            styles.append((n, n + len(line), style))
            n += len(line) + 1
            content.append(line)

        content = '\n'.join(content)
        self.document = document.FormattedDocument(content)
        self.document.set_style(0, len(content), {'align': self.halign})
        for s, e, attrs in styles:
            self.document.set_style(s, e, attrs)

        # render the text lines to our batch
        self.batch = graphics.Batch()
        self.layout = layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign = self.valign
        if self.valign == 'center':
            self.layout.y = vh//2
        elif self.valign == 'bottom':
            self.layout.y = 0
        else:
            self.layout.y = vh

    def on_next(self):
        if self.exposed == len(self.blocks):
            return False
        s, e, color = self.blocks[self.exposed]
        FadeIn(self, s, e, rgb=color[:3], duration=.5)
        self.exposed += 1
        return True

    def on_previous(self):
        if self.exposed == 0:
            return False
        self.exposed -= 1
        s, e, color = self.blocks[self.exposed]
        #FadeOut(self, s, e, rgb=color[:3])
        self.document.set_style(s, e, dict(color=color[:3] + (0,)))

        return True

    def on_leave(self):
        for e in self.effects.values(): pyglet.clock.unschedule(e)
        self.effects = {}
        self.document = None
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

config.add_section('text', dict((k, v) for k, t, v in TextPage.config))

