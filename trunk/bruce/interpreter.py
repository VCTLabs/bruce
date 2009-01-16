import sys
import code

from docutils import nodes
from docutils.parsers.rst import directives

import pyglet
from pyglet.gl import *

from cocos.director import director

#
# Python Interpreter directive
#
class interpreter(nodes.Special, nodes.Invisible, nodes.Element):
    '''Document tree node representing Python interpreter a directive.
    '''
    def get_interpreter(self, stylesheet):
        # XXX allow to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if self.has_key('width'):
            kw['width'] = int(self['width'])
        if self.has_key('height'):
            kw['height'] = int(self['height'])
        if self.has_key('sysver'):
            kw['sysver'] = True

        return InterpreterElement(self.rawsource, stylesheet, **kw)

def interpreter_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ interpreter('\n'.join(arguments), **options) ]
interpreter_directive.arguments = (0, 0, 0)
interpreter_directive.options = dict(
     width=directives.positive_int,
     height=directives.positive_int,
     sysver=directives.flag,
)
interpreter_directive.content = True
directives.register_directive('interpreter', interpreter_directive)

class MyScrollableTextLayoutGroup(pyglet.text.layout.ScrollableTextLayoutGroup):
    '''Extend the base pyglet scrollable text layout group to handle being
    embedded in (and thus scrolled by) another scrollable text layout. This
    affects the scissor clipping region.
    '''
    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT | GL_SCISSOR_BIT | GL_CURRENT_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Disable scissor to check culling.
        glEnable(GL_SCISSOR_TEST)

        # offset the scissor based on the parent layout's screen translation
        parent_x = self.parent_group.translate_x
        parent_y = self.parent_group.translate_y
        glScissor(parent_x + self._clip_x - 1,
                  parent_y + self._clip_y - self._clip_height,
                  self._clip_width + 1,
                  self._clip_height)
        glTranslatef(self.translate_x, self.translate_y, 0)

class ScrolledIncrementalTextLayout(pyglet.text.layout.IncrementalTextLayout):
    '''Override to alter the default Groups assigned to the Layout so we use
    MyScrollableTextLayoutGroup.
    '''
    def _init_groups(self, group):
        # override with our scrolledd scrollable ... er layout
        self.top_group = MyScrollableTextLayoutGroup(group)
        self.background_group = pyglet.graphics.OrderedGroup(0, self.top_group)
        self.foreground_group = pyglet.text.layout.TextLayoutForegroundGroup(1, self.top_group)
        self.foreground_decoration_group = \
            pyglet.text.layout.TextLayoutForegroundDecorationGroup(2, self.top_group)

    def get_screen_rect(self):
        '''Convenience function to determine the pixels being used on-screen
        by this Layout.
        '''
        tg = self.top_group
        parent_x = tg.parent_group.translate_x
        parent_y = tg.parent_group.translate_y
        return (parent_x + tg._clip_x - 1,
                  parent_y + tg._clip_y - tg._clip_height,
                  tg._clip_width + 1,
                  tg._clip_height)

class Output:
    '''Utility for capturing stdout from an interactive session.
    '''
    def __init__(self, display, realstdout):
        self.out = display
        self.realstdout = realstdout
        self.data = ''

    def write(self, data):
        self.out(data)

# XXX put this in a thread
# XXX but how to supervise / terminate it?
class MyInterpreter(code.InteractiveInterpreter):
    '''Extend the base interpreter by capturing the output so we may display it
    using OpenGL.
    '''
    def __init__(self, locals, display):
        self.write = display
        code.InteractiveInterpreter.__init__(self, locals=locals)

    def execute(self, input):
        old_stdout = sys.stdout
        sys.stdout = Output(self.write, old_stdout)
        more = self.runsource(input)
        sys.stdout = old_stdout
        return more


class InterpreterElement(pyglet.text.document.InlineElement):
    prompt = ">>> "
    prompt_more = "... "

    def __init__(self, content, stylesheet, width=1024, height=400, sysver=False):
        self.stylesheet = stylesheet.copy()

        # figure style information
        self.style = self.stylesheet['default'].copy()
        self.style.update(self.stylesheet['literal'])
        self.style.update(self.stylesheet['literal_block'])

        self.width_spec = self.width = width
        self.height_spec = self.height = height
        self.dpi = 96

        # set up the interpreter
        if sysver:
            self.content = sys.version + '\n' + self.prompt
        else:
            self.content = self.prompt
        self.interpreter = MyInterpreter({}, self._write)
        self.current_input = []
        self.history = ['']
        self.history_pos = 0

        # format the code
        self.document = pyglet.text.document.FormattedDocument(self.content)
        s = self.style.copy()
        del s['background_color']
        self.document.set_style(0, len(self.document.text), s)

        # sure there's only one run *now*
        iter = self.document.get_style_runs('color')
        self.color_runs = [[s, e, c]
            for s, e, c in iter.ranges(0, len(self.document.text))]

        # remember the start of the line for later command handling and cursor movement
        self.start_of_line = len(self.document.text)

        self.quad = None
        self.caret = None
        self.opacity = 255

        # figure the line height
        l = pyglet.text.Label('My', font_size=self.style['font_size'],
            font_name=self.style['font_name'], dpi=self.dpi)
        super(InterpreterElement, self).__init__(l.content_height,
            l.content_height - self.height, self.width)

    def set_scale(self, scale):
        self.width = int(self.width_spec * scale)
        self.height = int(self.height_spec * scale)
        self.dpi = int(scale * 96)

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

        # force re-layout if we're laid out
        if self.layout is not None:
            self.layout.delete()
            self.layout = None
            self.quad.delete()
            self.caret.delete()

    def set_opacity(self, layout, opacity):
        self.opacity = int(opacity)

        # background
        if self.quad is not None:
            c = self.style['background_color']
            v = opacity/255.
            c = c[:3] + (int(v * c[3]),)
            self.quad.colors[:] = c * 4

        # text color
        for s, e, color in self.color_runs:
            color = color[:3] + (int(v * color[3]),)
            self.document.set_style(s, e, dict(color=color))

        # caret too
        if self.caret is not None:
            self.caret.visible = bool(self.opacity)


    layout = None
    def place(self, layout, x, y):
        # XXX only do this when active
        director.window.push_handlers(self)

        # XXX maybe allow myself to be added to multiple layouts for whatever that's worth
        if self.layout is not None:
            # just position
            self.layout.begin_update()
            self.layout.x = x
            self._placed_y = y
            self.layout.y = y
            self.layout.anchor_y = 'bottom'
            self.layout.end_update()
            return

        c = self.style['background_color']
        v = self.opacity/255.
        c = c[:3] + (int(v * c[3]),)
        self.quad = layout.batch.add(4, GL_QUADS, layout.top_group,
            ('c4B', c*4),
            ('v2i', (x, y, x, y+self.height, x+self.width, y+self.height, x+self.width, y))
        )
        self.layout = ScrolledIncrementalTextLayout(self.document,
            self.width, self.height, dpi=self.dpi, multiline=True, batch=layout.batch,
            group=layout.top_group)

        # position
        self.layout.begin_update()
        self.layout.x = x
        self.layout.y = y
        self._placed_y = y
        self.layout.anchor_y = 'bottom'
        self.layout.end_update()

        # store off a reference to the surrounding layout's group so we can
        # modify our scissor based on its screen position (ugh)
        self.layout.top_group.parent_group = layout.top_group

        self.caret = pyglet.text.caret.Caret(self.layout, color=self.style['color'][:3])
        self.caret.on_activate()
        self.caret.position = len(self.document.text)
        if not self.opacity:
            self.caret.visible = False

    def remove(self, layout):
        director.window.pop_handlers()
        self.layout.delete()
        self.layout = None
        self.quad.delete()
        self.quad = None
        self.caret.delete()
        self.caret = None

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.TAB:
            return self.caret.on_text('\t')
        elif symbol in (pyglet.window.key.ENTER, pyglet.window.key.NUM_ENTER):
            # write the newline
            self._write('\n')

            line = self.document.text[self.start_of_line:]
            if line == 'help()':
                line = 'print "help() not supported, sorry!"'
            line = line.rstrip()
            self.current_input.append(line)
            self.history_pos = len(self.history)
            if line:
                self.history[self.history_pos-1] = line
                self.history.append('')
            more = self.interpreter.execute('\n'.join(self.current_input))
            if more:
                self._write(self.prompt_more)
            else:
                self.current_input = []
                self._write(self.prompt)
            self.start_of_line = len(self.document.text)
            self.caret.position = len(self.document.text)
        elif symbol == pyglet.window.key.SPACE:
            pass
        else:
            return pyglet.event.EVENT_UNHANDLED
        return pyglet.event.EVENT_HANDLED

    def on_text(self, symbol):
        # squash carriage return - we already handle them above
        if symbol == '\r':
            return pyglet.event.EVENT_HANDLED

        self._scroll_to_bottom()
        return self.caret.on_text(symbol)

    def on_text_motion(self, motion):
        at_sol = self.caret.position == self.start_of_line

        if motion == pyglet.window.key.MOTION_UP:
            # move backward in history, storing the current line of input
            # if we're at the very end of time
            line = self.document.text[self.start_of_line:]
            if self.history_pos == len(self.history)-1:
                self.history[self.history_pos] = line
            self.history_pos = max(0, self.history_pos-1)
            self.document.delete_text(self.start_of_line,
                len(self.document.text))
            self._write(self.history[self.history_pos])
            self.caret.position = len(self.document.text)
        elif motion == pyglet.window.key.MOTION_DOWN:
            # move forward in the history
            self.history_pos = min(len(self.history)-1, self.history_pos+1)
            self.document.delete_text(self.start_of_line,
                len(self.document.text))
            self._write(self.history[self.history_pos])
            self.caret.position = len(self.document.text)
        elif motion == pyglet.window.key.MOTION_BACKSPACE:
            # can't delete the prompt
            if not at_sol:
                return self.caret.on_text_motion(motion)
        elif motion == pyglet.window.key.MOTION_LEFT:
            # can't move back beyond start of line
            if not at_sol:
                return self.caret.on_text_motion(motion)
        elif motion == pyglet.window.key.MOTION_PREVIOUS_WORD:
            # can't move back word beyond start of line
            if not at_sol:
                return self.caret.on_text_motion(motion)
        else:
            return self.caret.on_text_motion(motion)
        return pyglet.event.EVENT_HANDLED

    def _write(self, s):
        self.document.insert_text(len(self.document.text), s, self.style)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # on key press always move the view to the bottom of the screen
        if self.layout.height < self.layout.content_height:
            self.layout.view_y = self.layout.content_height - self.layout.height
        if self.caret.position < self.start_of_line:
            self.caret.position = len(self.document.text)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.layout is None:
            # not on-screen at all
            return
        sx, sy, sw, sh = self.layout.get_screen_rect()
        if x < sx or x > sx + sw: return
        if y < sy or y > sy + sh: return
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 32
        return True

