import time

import pyglet

class AutoPlayer(object):
    initialised = False
    delay = None

    def __init__(self, options, pres):
        self.options = options
        self.pres = pres

    def initialise(self, second_run=False):
        '''Split this out from __init__ so the timings may be set up
        *after* the first page is displayed, thus not being affected by
        parse / setup time.

        The second_run flag indicates that the first page needs to have a delay
        incorporated as well.
        '''
        self.start = time.time()
        base = self.start
        if self.options.playback:
            if second_run:
                # XXX eugh defaulting to 1s for recording playback
                base += 1
            times = [float(l.split()[0]) for l in open(self.options.playback)]
            self.times = [base + t-times[0] for t in times]
            if not second_run:
                del self.times[0]
        else:
            if second_run:
                base += self.delay
            self.delay = float(self.options.playspeed)
            num_pages = len(self.pres.pages)
            self.times = [base + n * self.delay
                for n in range(num_pages)]
            if not second_run:
                del self.times[0]

    def on_page_changed(self, page, num):
        if not self.initialised:
            self.initialise()
            self.initialised = True
        elif num == len(self.pres.pages) - 1:
            # XXX eugh defaulting to 1s for recording playback
            delay = self.delay or 1
            if self.options.loop:
                self.initialise(second_run=True)
                def f(dt, dir, self=self):
                    self.pres.change_page(dir)
                pyglet.clock.schedule_once(f, self.delay, -len(self.pres.pages))
            elif self.options.once:
                # quit after we've displayed this page
                def f(dt):
                    pyglet.app.exit()
                pyglet.clock.schedule_once(f, self.delay)

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

