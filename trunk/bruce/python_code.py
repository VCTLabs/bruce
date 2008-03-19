import sys
import os
import subprocess
import tempfile
import threading
import time
import Queue
import errno
from cgi import escape as html_quote

import pyglet
from pyglet import graphics
from pyglet import text
from pyglet.text import caret, document, layout

from bruce import config
from bruce import page

# XXX add option to minimize on launch and restore when process quits

# XXX: When should subprocess, thread and tempfile cleanup happen? 
# Upon leaving the slide? 
# Upon finishing the talk?

class PythonCodePage(page.PageWithTitle, page.ScrollableLayoutPage):
    '''Runs an editor for a Python script which is executable.
    '''
    config = (
        ('title', str, 'BruceEdit(tm) Python Source Editor'),
        ('title.font_name', str, 'Arial'),
        ('title.font_size', float, 24),
        ('title.color', tuple, (200, 255, 255, 255)),
        # fits 80 columns across 1024 pixels
        ('code.font_name', str, 'Courier New'),
        ('code.font_size', float, 20),
        ('code.color', tuple, (200, 200, 200, 255)),
        ('caret.color', tuple, (200, 200, 200)),
    )
    name = 'pycode'

    def __init__(self, content, **kw):
        super(PythonCodePage, self).__init__(content, **kw)
        self._python = None

    @classmethod
    def as_html(cls, content, **kw):
        inst = cls(content, **kw)
        if not inst.content:
            return 'python script'
        return '<pre>%s</pre>'%html_quote(inst.content)

    def on_enter(self, vw, vh):
        super(PythonCodePage, self).on_enter(vw, vh)

        # format the code
        self.document = document.UnformattedDocument(self.content)
        self.document.set_style(0, 1, {
            'font_name': self.cfg['code.font_name'],
            'font_size': self.cfg['code.font_size'],
            'color': self.cfg['code.color'],
        })

        self.batch = graphics.Batch()

        self.generate_title()

        # generate the document
        self.layout = layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign = 'top'

        self.caret = caret.Caret(self.layout, color=self.cfg['caret.color'])
        self.caret.on_activate()

        self.on_resize(vw, vh)

    def on_resize(self, vw, vh):
        self.viewport_width, self.viewport_height = vw, vh

        if self.title_label:
            self.title_label.x = vw //2
            self.title_label.y = vh = vh - self.title_label.content_height

        self.layout.begin_update()
        self.layout.x = 2
        self.layout.width = vw - 4
        self.layout.height = vh
        self.layout.valign = 'top'
        self.layout.y = vh
        self.layout.end_update()
        self.caret.position = len(self.document.text)

    def on_leave(self):
        self.content = self.document.text
        self.document = None
        self.title_label = None
        self.layout = None
        self.batch = None
        self.caret = None

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.TAB:
            return self.on_text('\t')
        elif symbol == pyglet.window.key.SPACE:
            pass
        elif self._python and symbol == pyglet.window.key.ENTER:
            return self.on_text('\n')
        elif symbol == pyglet.window.key.ESCAPE:
            if self._python is not None:
                self._subprocess_finished()
            else:
                return pyglet.event.EVENT_UNHANDLED
        elif symbol == pyglet.window.key.F4 and not self._python:
            self._source = self.document.text
            temp_fd, temp_name = tempfile.mkstemp(prefix='bruce-temp', 
                suffix='.py')
            f = os.fdopen(temp_fd, 'w')
            f.write(self._source)
            f.close()
            args = [sys.executable, '-u', temp_name]
            self._python = subprocess.Popen(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            self.title_label.text = 'Running... output below'
            self.document.text = '> %s\n'%' '.join(args)
            self.caret.on_deactivate()
            self.stdin = []

            self._stdout_queue = Queue.Queue()
            t = threading.Thread(target=thread_read_to_queue, 
                    args = (self._python.stdout, self._stdout_queue))
            t.setDaemon(True)
            t.start()

            self._stdin_queue = Queue.Queue()
            t = threading.Thread(target=thread_queue_to_write, 
                    args = (self._python.stdin, self._stdin_queue))
            t.setDaemon(True)
            t.start()
        else:
            return pyglet.event.EVENT_UNHANDLED
        return pyglet.event.EVENT_HANDLED

    def update(self, dt):
        if self._python is not None:
            p = self._python

            # check for termination
            returncode = p.poll()
            if returncode is not None:
                self.title_label.text = '(returned %s) - hit escape' % (
                    returncode)

            stdout = []
            # XXX: implement stderr capture
            stderr = [] 

            while True:
                try:
                    temp_char = self._stdout_queue.get_nowait()
                    stdout.append(temp_char)
                except Queue.Empty:
                    break

            # All data exchanged.  Translate lists into strings.
            if stdout:
                self._write(''.join(stdout))
            if stderr:
                self._write(''.join(stderr))

    def _subprocess_finished(self):
        self.document.text = self._source
        self.document.set_style(0, len(self.document.text), {
            'font_name': self.cfg['code.font_name'],
            'font_size': self.cfg['code.font_size'],
            'color': self.cfg['code.color'],
        })
        self.caret.on_activate()
        self.title_label.text = '%s (python returned %s)'%(self.title,
            self._python.returncode)
        self._python = None

    def on_text(self, symbol):
        if self._python is not None:
            self._write(symbol)
            self._stdin_queue.put(symbol)
            return pyglet.event.EVENT_HANDLED
        return self.caret.on_text(symbol)

    def on_text_motion(self, motion):
        return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        return self.caret.on_text_motion_select(motion)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        return self.caret.on_mouse_drag(x, y, dx, dy, button, modifiers)

    def _write(self, s):
        self.document.insert_text(len(self.document.text), s)
        #, {
            #'font_name': self.cfg['code.font_name'],
            #'font_size': self.cfg['code.font_size'],
            #'color': self.cfg['code.color'],
        #})
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        # on key press always move the view to the bottom of the screen
        if self.layout.height < self.layout.content_height:
            self.layout.valign = 'bottom'
            self.layout.y = 0
            self.layout.view_y = 0

    def draw(self):
        self.batch.draw()

def thread_read_to_queue(pipe, queue):
    while True:
        char = pipe.read(1)
        queue.put(char)

def thread_queue_to_write(pipe, queue):
    while True:
        char = queue.get()
        try:
            pipe.write(char)
        except IOError: # subprocess terminated
            pass

config.add_section('pycode', dict((k, v) for k, t, v in PythonCodePage.config))

