from docutils import nodes
from docutils.parsers.rst import directives

import pyglet

#
# Video directive
#
class video(nodes.Special, nodes.Invisible, nodes.Element):
    def get_video(self):
        # XXX allow to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if self.has_key('width'):
            kw['width'] = int(self['width'])
        if self.has_key('height'):
            kw['height'] = int(self['height'])
        if self.has_key('loop'):
            kw['loop'] = True

        return VideoElement(self.rawsource, **kw)

def video_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ video('\n'.join(arguments), **options) ]
video_directive.arguments = (1, 0, 1)
video_directive.options = dict(
     width=directives.positive_int,
     height=directives.positive_int,
     loop=directives.flag,
)
video_directive.content = True
def register_directives():
    directives.register_directive('video', video_directive)

class VideoElement(pyglet.text.document.InlineElement):
    def __init__(self, video_filename, width=None, height=None, loop=False):
        self.video_filename = video_filename

        self.width_spec = width
        self.height_spec = height

        video = pyglet.resource.media(self.video_filename)
        self.loop = loop
        assert video.video_format
        video_format = video.video_format

        # determine dimensions
        self.video_width = video_format.width
        self.video_height = video_format.height
        if video_format.sample_aspect > 1:
            self.video_width *= video_format.sample_aspect
        elif video_format.sample_aspect < 1:
            self.video_height /= video_format.sample_aspect

        # scale based on dimensions supplied
        if height is not None and width is None:
            scale = height / float(self.video_height)
            width = int(scale * self.video_width)
        elif width is not None:
            scale = width / float(self.video_width)
            height = int(scale * self.video_height)

        self.width = width or self.video_width
        self.height = height or self.video_height

        self.vertex_lists = {}
        self.opacity = 255

        super(VideoElement, self).__init__(self.height, 0, self.width)

    def set_opacity(self, layout, opacity):
        self.opacity = int(opacity)
        self.vertex_lists[layout].colors[:] = [255, 255, 255, self.opacity]*4

    def set_scale(self, scale):
        width, height = self.width_spec, self.height_spec

        # scale based on dimensions supplied
        if height is not None and width is None:
            scale = height / float(self.video_height)
            width = int(scale * self.video_width)
        elif width is not None:
            scale = width / float(self.video_width)
            height = int(scale * self.video_height)

        self.width = width or self.video_width
        self.height = height or self.video_height

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

        # assumes only one player (layout) active at a time
        self.player_needed = None

    player = video = None
    def set_active(self, active):
        if not active:
            self.player.next()
            self.player = None
            self.video = None
            self.vertex_list.delete()
            self.vertex_list = None
            return

        if self.player_needed is None:
            return

        self.video = pyglet.resource.media(self.video_filename)

        layout, x, y = self.player_needed

        # create the player
        self.player = pyglet.media.Player()
        self.player.queue(self.video)
        if self.loop:
            self.player.eos_action = self.player.EOS_LOOP
        else:
            self.player.eos_action = self.player.EOS_PAUSE
        self.player.play()

        texture = self.player.texture

        group = pyglet.sprite.SpriteGroup(texture,
            pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA,
            layout.top_group)

        # set up rendering the player texture
        x1 = int(x)
        y1 = int(y + self.descent)
        x2 = int(x + self.width)
        y2 = int(y + self.height + self.descent)
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('c4B', (255, 255, 255, self.opacity) * 4),
            ('t3f', texture.tex_coords))
        self.vertex_list = vertex_list

    def set_opacity(self, opacity):
        self.opacity = int(opacity)
        self.vertex_list.colors[:] = [255, 255, 255, self.opacity]*4

    def place(self, layout, x, y):
        self.player_needed = (layout, x, y)

    def remove(self, layout):
        self.player_needed = None

