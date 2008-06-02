import sys
import code

from docutils import nodes
from docutils.parsers.rst import directives

import pyglet
from pyglet.gl import *

#
# Python Interpreter directive
#
class interpreter(nodes.Special, nodes.Invisible, nodes.Element):
    def get_interpreter(self):
        # XXX allow to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if self.has_key('width'):
            kw['width'] = int(self['width'])
        if self.has_key('height'):
            kw['height'] = int(self['height'])
        if self.has_key('sysver'):
            kw['sysver'] = True

        return InterpreterElement(self.rawsource, **kw)

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
    def set_state(self):
        glPushAttrib(GL_ENABLE_BIT | GL_SCISSOR_BIT | GL_CURRENT_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Disable scissor to check culling.
        glEnable(GL_SCISSOR_TEST)

        # offset the scissor based on the parent layout's screen translation
        parent_x = self.parent_group.translate_x
        parent_y = self.parent_group.translate_y
        glScissor(parent_x + self._scissor_x - 1,
                  parent_y + self._scissor_y - self._scissor_height,
                  self._scissor_width + 1,
                  self._scissor_height)
        glTranslatef(self.translate_x, self.translate_y, 0)

class ScrolledIncrementalTextLayout(pyglet.text.layout.IncrementalTextLayout):
    def _init_groups(self, group):
        # override with our scrolledd scrollable ... er layout
        self.top_group = MyScrollableTextLayoutGroup(group)
        self.background_group = pyglet.graphics.OrderedGroup(0, self.top_group)
        self.foreground_group = pyglet.text.layout.TextLayoutForegroundGroup(1, self.top_group)
        self.foreground_decoration_group = \
            pyglet.text.layout.TextLayoutForegroundDecorationGroup(2, self.top_group)

    def get_screen_rect(self):
        tg = self.top_group
        parent_x = tg.parent_group.translate_x
        parent_y = tg.parent_group.translate_y
        return (parent_x + tg._scissor_x - 1,
                  parent_y + tg._scissor_y - tg._scissor_height,
                  tg._scissor_width + 1,
                  tg._scissor_height)

class Output:
    def __init__(self, display, realstdout):
        self.out = display
        self.realstdout = realstdout
        self.data = ''

    def write(self, data):
        self.out(data)

# XXX put this in a thread
class MyInterpreter(code.InteractiveInterpreter):
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

    def __init__(self, content, width=800, height=300, sysver=False):
        self.width = width
        self.height = height

        # set up the interpreter
        if sysver:
            self.content = sys.version + '\n' + self.prompt
        else:
            self.content = self.prompt
        self.interpreter = MyInterpreter({}, self._write)
        self.current_input = []
        self.history = ['']
        self.history_pos = 0

        super(InterpreterElement, self).__init__(self.height, 0, self.width)

    def on_enter(self, w, h):
        # format the code
        self.document = pyglet.text.document.FormattedDocument(self.content)
        self.document.set_style(0, len(self.document.text), {
            'font_name': 'Courier New',
            'font_size': 20, 
            'color': (0, 0, 0, 255),
        })
        self.start_of_line = len(self.document.text)

    def on_leave(self):
        self.document = None

    layout = None
    def place(self, layout, x, y):
        # XXX allow myself to be added to multiple layouts for whatever that's worth
        if self.layout is not None:
            # just position
            self.layout.begin_update()
            self.layout.x = x
            self._placed_y = y
            self.layout.y = y + self.height
            self.layout.anchor_y = 'top'
            self.layout.end_update()
            return

        self.quad = layout.batch.add(4, GL_QUADS, layout.top_group,
            ('c4B', (220, 220, 220, 255)*4),
            ('v2i', (x, y, x, y+self.height, x+self.width, y+self.height, x+self.width, y))
        )
        self.layout = ScrolledIncrementalTextLayout(self.document,
            self.width, self.height, multiline=True, batch=layout.batch,
            group=layout.top_group)

        # position
        self.layout.begin_update()
        self.layout.x = x
        self.layout.y = y + self.height
        self._placed_y = y
        self.layout.anchor_y = 'top'
        self.layout.end_update()

        # store off a reference to the surrounding layout's group so we can
        # modify our scissor based on its screen position (ugh)
        self.layout.top_group.parent_group = layout.top_group

        self.caret = pyglet.text.caret.Caret(self.layout, color=(0, 0, 0))
        self.caret.on_activate()
        self.caret.position = len(self.document.text)

    def remove(self, layout):
        pass

    def on_leave(self):
        self.layout.delete()
        self.layout = None
        self.quad.delete()
        self.caret.delete()

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
        self.document.insert_text(len(self.document.text), s, {
            'font_name': 'Courier New',
            'font_size': 20,
            'color': (0, 0, 0, 255),
        })
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # on key press always move the view to the bottom of the screen
        if self.layout.height < self.layout.content_height:
            self.layout.view_y = self.layout.content_height - self.layout.height
        if self.caret.position < self.start_of_line:
            self.caret.position = len(self.document.text)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        sx, sy, sw, sh = self.layout.get_screen_rect()
        if x < sx or x > sx + sw: return
        if y < sy or y > sy + sh: return
        self.layout.view_x -= scroll_x
        self.layout.view_y += scroll_y * 32
        return True

