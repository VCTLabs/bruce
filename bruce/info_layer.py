import time

import pyglet
import cocos
from cocos.director import director

class InfoLayer(cocos.layer.Layer):
    def __init__(self, show_timer, show_count, num_pages):
        super(InfoLayer, self).__init__()

        self.show_timer = show_timer
        self.show_count = show_count
        self.num_pages = num_pages
        self.page_num = 0
        self.start_time = None

        self.batch = pyglet.graphics.Batch()
        y = 0
        if show_timer:
            self.timer_label = pyglet.text.Label('--:--',
                font_name='Courier New', font_size=24,
                color=(128, 128, 128, 128),
                anchor_x='right', anchor_y='bottom', batch=self.batch,
                x=director.window.width, y=0)
            y = self.timer_label.content_height
            pyglet.clock.schedule(self.update)

        if show_count:
            self.count_label = pyglet.text.Label(
                '%d/%d'%(self.page_num+1, self.num_pages),
                font_name='Courier New', font_size=24,
                color=(128, 128, 128, 128),
                anchor_x='right', anchor_y='bottom', batch=self.batch,
                x=director.window.width, y=y)

    def on_resize(self, w, h):
        y = 0
        if show_timer:
            self.timer_label.x = w
            y = self.timer_label.content_height
        if show_count:
            self.count_label.x = w
            self.count_label.y = y

    def on_page_changed(self, page, page_num):
        # start the timer if we're displaying one
        if self.show_timer and self.start_time is None:
            self.start_time = time.time()

        self.page_num = page_num

        if self.show_count:
            self.count_label.text = '%d/%d'%(self.page_num+1, self.num_pages)

        if self not in page:
            page.add(self, z=.5)

    def update(self, dt):
        if self.start_time is not None:
            t = time.time() - self.start_time
            self.timer_label.text = '%02d:%02d'%(t//60, t%60)

    def draw(self):
        self.batch.draw()

