__version__ = '2.0beta3'

import os
import sys
import time
from cgi import escape as html_quote

import pyglet

from bruce import parser
from bruce import presentation
from bruce import resource
from bruce import config

def _window(width, height, fullscreen, screen):
    display = pyglet.window.get_platform().get_default_display()
    screen = display.get_screens()[screen]
    if fullscreen:
        win = pyglet.window.Window(fullscreen=fullscreen, screen=screen)
        # XXX on_resize to transform to fit width / height from above
        return win
    else:
        return pyglet.window.Window(width=width, height=height, screen=screen)

def _run(win, content, **kw):
    p = presentation.Presentation(win, parser.parse(content), **kw)
    win.push_handlers(p)
    pyglet.app.run()

def run(filename, fullscreen=False, screen=0, width=1024, height=768, **kw):
    directory = os.path.abspath(os.path.dirname(filename))
    config.set('directory', directory)
    resource.loader.path.append(directory)
    resource.loader.reindex()
    _run(_window(width, height, fullscreen, screen), file(filename).read(), **kw)

def runstring(content, fullscreen=False, screen=0, width=1024, height=768, **kw):
    _run(_window(width, height, fullscreen, screen), content, **kw)

def notes(filename, out_file='', columns=2):
    directory = os.path.abspath(os.path.dirname(filename))
    config.set('directory', directory)
    resource.loader.path.append(directory)
    resource.loader.reindex()
    pages = parser.parse(file(filename).read(), html=True)
    if out_file:
        o = file(out_file, 'w')
    else:
        o = sys.stdout
    print >>o, '''<html><head><base href="%s">
    <title>Presentation notes for %s</title>
    <style>
    table {
        border: thin solid gray;
        border-collapse: separate;
        border-spacing: 0px 0px;
    }
    td {
        border: thin solid gray;
    }
    pre {
        margin: 0px;
    }
    .container {
        position: relative;
        width: 100%%;
        height: 100%%;
    }
    .pagenum {
        background: #ddd;
        color: white;
        /* font-size: 200%%; */
        position: absolute;
        z-index: 1;
        right: 0px;
        bottom: 0px;
    }

    .content {
        z-index: 2;
        position: relative;
    }

    .note {
        z-index: 2;
        position: relative;
        font-size: 75%%;
        font-style: italic;
    }
    </style></head><body><table><tr>'''%(directory, filename)
    n = 0
    for page, note in pages:
        if not page:
            continue
        print >>o, '<td width="%d%%"valign="top">'%(100//columns,)
        print >>o, '<div class="container">'
        print >>o, '<div class="pagenum">%s</div>'%(n+1)
        print >>o, '<div class="content">%s</div>'%page.encode('ascii',
                'xmlcharrefreplace')
        if note:
            note = '<br>\n'.join(html_quote(n) for n in note)
            print >>o, '<div class="note">%s</div>'%note.encode('ascii',
                'xmlcharrefreplace')
        print >>o, '</div></td>'
        if n%columns == columns-1: print >>o, '</tr>'
        n += 1
    if n%columns != columns-1: print >>o, '</tr>'
    print >>o, '</table>'
    print >>o, '''<em>Generated by Bruce, The Presentation Tool (version %s)
        on %s'''%(__version__, time.asctime())
    print >>o, '</body></html>'

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-f", "--fullscreen", dest="fullscreen",
                      action="store_true", default=False,
                      help="run in fullscreen mode")
    p.add_option("-t", "--timer", dest="timer",
                      action="store_true", default=False,
                      help="display a timer")
    p.add_option("-p", "--pagecount", dest="page_count",
                      action="store_true", default=False,
                      help="display page numbers")
    p.add_option("-s", "--startpage", dest="start_page",
                      default="1",
                      help="start at page N (default 1)")
    p.add_option("-S", "--screen", dest="screen",
                      default="1",
                      help="display on screen (default 1)")
    p.add_option("-n", "--notes", dest="notes",
                      action="store_true", default=False,
                      help="generate HTML notes (do not run presentation)")
    p.add_option("-o", "--out-file", dest="out_file",
                      default="",
                      help="filename to write notes to (default stdout)")
    p.add_option("-c", "--columns", dest="columns",
                      default="2",
                      help="number of columns in notes (default 2)")
    p.add_option("-v", "--version", dest="version",
                      action="store_true", default=False,
                      help="display version and quit")
    p.add_option("-d", "--display-source", dest="source",
                      action="store_true", default=False,
                      help="display page source in terminal")
    p.add_option("-w", "--window-size", dest="window_size",
                      default="1024x768",
                      help="size of the window when not fullscreen")

    '''
    Disabled because it's not pretty
    p.add_option("-z", "--zoom", dest="zoom",
                      default="0",
                      help="zoom display to fill fullscreen")
    '''

    (options, args) = p.parse_args()

    if options.version:
        print __version__
    elif options.notes:
        notes(args[0], options.out_file, int(options.columns))
    else:
        display = pyglet.window.get_platform().get_default_display()
    screen = int(options.screen)-1
    screen = display.get_screens()[screen]
    width, height = map(int, options.window_size.split('x'))
    width = min(width, screen.width)
    height = min(height, screen.height)
    run(args[0], fullscreen=options.fullscreen,
        show_timer=options.timer, show_count=options.page_count,
        start_page=int(options.start_page)-1, show_source=options.source,
        screen=int(options.screen)-1, width=width, height=height)
