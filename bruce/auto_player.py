import time

import pyglet

class AutoPlayer(object):
    initialised = False
    delay = None

    def __init__(self, options, pres):
        self.options = options
        self.pres = pres

    def initialise(self):
        '''Split this out from __init__ so the timings may be set up
        *after* the first page is displayed, thus not being affected by
        parse / setup time.
        '''
        self.start = time.time()
        self.loop = self.options.loop
        if self.options.playback:
            times = [float(l.split()[0]) for l in open(self.options.playback)]
            self.times = [t-times[0]+self.start for t in times]
            del self.times[0]
        else:
            self.delay = int(self.options.playspeed)
            num_pages = len(self.pres.pages)
            self.times = [self.start + n * self.delay
                for n in range(num_pages)]
            del self.times[0]

    def on_page_changed(self, page, num):
        if not self.initialised:
            self.initialise()
            self.initialised = True
        elif num == len(self.pres.pages) - 1 and self.loop:
            self.initialise()
            def f(dt, dir, self=self):
                self.pres.change_page(dir)
            pyglet.clock.schedule_once(f, self.delay, -len(self.pres.pages))

        if not self.times:
            return

        next = self.times.pop(0)
        dt = next - time.time()

        # XXX handle backward, use page num from screenshot?
        # XXX handle non-page changes?
        if dt > 0:
            def f(dt, dir, self=self):
                self.pres.change_page(dir)
            pyglet.clock.schedule_once(f, dt, 1)
        else:
            self.pres.change_page(1)

