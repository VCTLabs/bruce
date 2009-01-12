
import os
import sys
import time
import re
from cgi import escape as html_quote

import pyglet
from cocos.director import director
from cocos import actions

from bruce import rst_parser
from bruce import presentation
from bruce import display_source
from bruce import style

def main():
    '''Run either the command-line or gui interface depending on whether any
    command-line arguments were provided.
    '''
    if len(sys.argv) > 1:
        cmd_line()
    else:
        GUI().run()

class GUI(object):
    '''Run a simple tk-based gui to select the file to display and control
    configuration options.
    '''
    def run(self):
        import Tkinter
        import tkFileDialog

        # lay out the basic GUI
        self.root = Tkinter.Tk()
        frame = Tkinter.Frame(self.root)
        frame.pack()

        Tkinter.Label(frame, text='Bruce, the Presentation Tool!').pack()

        self.fullscreen = Tkinter.IntVar()
        Tkinter.Checkbutton(frame, text='Fullscreen?',
            variable=self.fullscreen).pack()

        # screen selection
        display = pyglet.window.get_platform().get_default_display()
        N = len(display.get_screens())
        self.screen = Tkinter.IntVar(0)
        if N > 1:
            for n in range(N):
                Tkinter.Radiobutton(frame, text="Display on screen %d"%(n+1),
                    variable=self.screen, value=n).pack()

        self.timer = Tkinter.IntVar()
        Tkinter.Checkbutton(frame, text='Show Timer?',
            variable=self.timer).pack()

        self.page_count = Tkinter.IntVar()
        Tkinter.Checkbutton(frame, text='Show Page Count?',
            variable=self.page_count).pack()

        self.bullet_mode = Tkinter.IntVar()
        Tkinter.Checkbutton(frame, text='Run in Bullet Mode?',
            variable=self.bullet_mode).pack()

        self.source = Tkinter.IntVar()
        Tkinter.Checkbutton(frame, text='Display source in console?',
            variable=self.source).pack()

        Tkinter.Button(frame, text='Play Presentation',
            command=self.go).pack()

        # determine which file we're displaying
        self.filename = tkFileDialog.askopenfilename(parent=self.root,
            filetypes=[('ReStructuredText Files', '.rst .txt'),
                       ('All Files', '.*')],
            title='Select your presentation file')
        if not self.filename:
            # no file selected, just exit
            self.root.destroy()
            return

        # run Tk's mainloop to handle the above GUI
        self.root.mainloop()

    def go(self):
        # close the Tk GUI
        self.root.destroy()

        # snarf off all the config information and run
        class options:
            fullscreen = self.fullscreen.get()
            timer = self.timer.get()
            page_count = self.page_count.get()
            screen = self.screen.get()
            bullet_mode = self.bullet_mode.get()
            source = self.source.get()
            # XXX options still to configure
            start_page = 1
            style = 'not specified'
            window_size = '1024x768'
        run(self.filename, options)

def cmd_line():
    '''Run a command-line interface to select the file to display and control
    configuration options.
    '''
    from optparse import OptionParser
    p = OptionParser(usage='usage: %prog [options] presentation')
    p.add_option("-f", "--fullscreen", dest="fullscreen",
                      action="store_true", default=False,
                      help="run in fullscreen mode")
    p.add_option("", "--screen", dest="screen",
                      default="1",
                      help="display on screen (1+, default 1)")
    p.add_option("-w", "--window-size", dest="window_size",
                      default="1024x768",
                      help="size of the window when not fullscreen")

    p.add_option("-v", "--version", dest="version",
                      action="store_true", default=False,
                      help="display version and quit")

    p.add_option("-t", "--timer", dest="timer",
                      action="store_true", default=False,
                      help="display a timer")
    p.add_option("-p", "--pagecount", dest="page_count",
                      action="store_true", default=False,
                      help="display page numbers")
    p.add_option("-s", "--startpage", dest="start_page",
                      default="1",
                      help="start at page N (1+, default 1)")
    p.add_option("-r", "--record", dest="record", default="",
                      help="record timing and screenshots")

    p.add_option("", "--playback", dest="playback", default="",
                      help="play back a presentation using timing.txt")

    p.add_option("-b", "--bullet-mode", dest="bullet_mode",
                      action="store_true", default=False,
                      help="run in bullet mode (page per bulet)")
    p.add_option("", "--style", dest="style", default="not specified",
                      help="specify style (name or filename)")
    p.add_option("", "--list-styles", dest="list_styles",
                      action="store_true", default=False,
                      help="list available style names")

    #p.add_option("-d", "--progress-screen", dest="progress_screen",
    #                  default=None,
    #                  help="display progress in screen (1+, default none)")
    p.add_option("-D", "--display-source", dest="source",
                      action="store_true", default=False,
                      help="display source in terminal")

    (options, args) = p.parse_args()

    if options.version:
        print __version__
        sys.exit(0)

    if options.list_styles:
        print 'Available built-in style names:'
        print '\n'.join(sorted(style.stylesheets.keys()))
        sys.exit(0)

    if not args:
        print 'Error: presentation filename required'
        print p.get_usage()
        sys.exit(1)

    #elif options.notes:
    #    notes(args[0], options.out_file, int(options.columns))

    run(args[0], options)

def run(filename, options):

    display = pyglet.window.get_platform().get_default_display()
    screen = int(options.screen)-1
    screen = display.get_screens()[screen]
    #progress_screen = None
    #if options.progress_screen:
    #    progress_screen = int(options.progress_screen)-1
    #    progress_screen = display.get_screens()[progress_screen]
    width, height = map(int, re.split('\D+', options.window_size))
    width = min(width, screen.width)
    height = min(height, screen.height)
    screen=int(options.screen)-1

    # add the presentation's directory to resource locations
    directory = os.path.abspath(os.path.dirname(filename))
    pyglet.resource.path.append(directory)
    pyglet.resource.reindex()

    # initialise the display
    display = pyglet.window.get_platform().get_default_display()
    screen = display.get_screens()[screen]
    if options.fullscreen:
        director.init(fullscreen=options.fullscreen,
            screen=screen, do_not_scale=True)
    else:
        director.init(width=width, height=height,
            screen=screen, do_not_scale=True)

    # grab the presentation content and parse into pages
    content = file(filename).read()
    if options.style == 'not specified':
        if options.bullet_mode:
            stylesheet = style.stylesheets['big-centered'].copy()
        else:
            stylesheet = style.stylesheets['default'].copy()
    else:
        stylesheet = style.get(options.style)

    # override some stuff because of recording
    stylesheet.set_recording(options.record)

    pages = rst_parser.parse(content, stylesheet=stylesheet,
        bullet_mode=options.bullet_mode)

    # run
    pres = presentation.Presentation(pages,
        show_timer=options.timer, show_count=options.page_count,
        start_page=int(options.start_page)-1,
        desired_size=(width, height))

    # listen for page changes if we're recording
    if options.record:
        if not os.path.exists(options.record):
            os.makedirs(options.record)
        open(os.path.join(options.record, 'timing.txt'), 'w').close()

        @pres.event
        def on_page_changed(page, num):
            # XXX record non-page-changes?
            def save(num=num):
                t = time.time()
                filename = 'screenshot-%d.png'%num
                f = open(os.path.join(options.record, 'timing.txt'), 'a')
                f.write('%.1f %s\n'%(t, filename))
                filename = os.path.join(options.record, filename)
                buffer = pyglet.image.get_buffer_manager().get_color_buffer()
                buffer.save(filename)
            # delay a moment to allow rendering to complete
            page.do(actions.Delay(.1) + actions.CallFunc(save))

    # playback?
    if options.playback:
        start_time = time.time()
        times = [float(l.split()[0]) for l in open(options.playback)]
        times = [t-times[0]+start_time for t in times]
        del times[0]
        @pres.event
        def on_page_changed(page, num):
            if not times:
                return
            dt = times.pop(0) - time.time()
            # XXX handle backward, use page num from screenshot?
            # XXX handle non-page changes?
            if dt > 0:
                page.do(actions.Delay(dt) + actions.CallFunc(pres.change_page, num+1))
            else:
                pres.change_page(num+1)


    director.window.push_handlers(pres)

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


if __name__ == '__main__':
    main()

