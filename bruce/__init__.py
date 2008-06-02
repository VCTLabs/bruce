__version__ = '3.0beta1'

import os
import sys
import time
from cgi import escape as html_quote

import pyglet

from bruce import rst_parser
from bruce import presentation
from bruce import display_source

def main():
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
                      help="start at page N (1+, default 1)")
    p.add_option("-S", "--screen", dest="screen",
                      default="1",
                      help="display on screen (1+, default 1)")
    #p.add_option("-n", "--notes", dest="notes",
    #                  action="store_true", default=False,
    #                  help="generate HTML notes (do not run presentation)")
    #p.add_option("-o", "--out-file", dest="out_file",
    #                  default="",
    #                  help="filename to write notes to (default stdout)")
    #p.add_option("-c", "--columns", dest="columns",
    #                  default="2",
    #                  help="number of columns in notes (default 2)")
    p.add_option("-v", "--version", dest="version",
                      action="store_true", default=False,
                      help="display version and quit")
    #p.add_option("-d", "--progress-screen", dest="progress_screen",
    #                  default=None,
    #                  help="display progress in screen (1+, default none)")
    p.add_option("-D", "--display-source", dest="source",
                      action="store_true", default=False,
                      help="display source in terminal")
    p.add_option("-w", "--window-size", dest="window_size",
                      default="1024x768",
                      help="size of the window when not fullscreen")

    (options, args) = p.parse_args()

    if options.version:
        print __version__
        sys.exit(0)

    elif not args:
        print 'Error: argument required'
        print p.get_usage()
        sys.exit(1)

    filename = args[0]

    #elif options.notes:
    #    notes(args[0], options.out_file, int(options.columns))

    display = pyglet.window.get_platform().get_default_display()
    screen = int(options.screen)-1
    screen = display.get_screens()[screen]
    #progress_screen = None
    #if options.progress_screen:
    #    progress_screen = int(options.progress_screen)-1
    #    progress_screen = display.get_screens()[progress_screen]
    width, height = map(int, options.window_size.split('x'))
    width = min(width, screen.width)
    height = min(height, screen.height)
    screen=int(options.screen)-1

    directory = os.path.abspath(os.path.dirname(filename))
    pyglet.resource.path.append(directory)
    pyglet.resource.reindex()

    display = pyglet.window.get_platform().get_default_display()
    screen = display.get_screens()[screen]
    if options.fullscreen:
        w = pyglet.window.Window(fullscreen=options.fullscreen,
            screen=screen)
        # on_resize to transform to fit width / height from above
        w._restore_size = (width, height)
    else:
        w = pyglet.window.Window(width=width, height=height,
            screen=screen)

    content = file(filename).read()
    pres = presentation.Presentation(w, rst_parser.parse(content),
        show_timer=options.timer, show_count=options.page_count,
        start_page=int(options.start_page)-1)

    w.push_handlers(pres)

#    if progress_screen is not None:
#        pw = min(1280, progress_screen.width)
#        ph = min(480, progress_screen.height)
#        if options.fullscreen:
#            pw = pyglet.window.Window(fullscreen=options.fullscreen,
#                screen=progress_screen)
#        else:
#            pw = pyglet.window.Window(pw, ph, screen=progress_screen)
#        prog = progress.Progress(pw, pres, content.decode('utf8'))
#        pw.push_handlers(prog)
#        pres.push_handlers(prog)
#        prog.push_handlers(pres)

    if options.source:
        pres.push_handlers(display_source.DisplaySource())

    # now that we're all set up, load up the first page
    pres.start_presentation()

    pyglet.app.run()


if __name__ == '__main__':
    main()

