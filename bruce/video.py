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
directives.register_directive('video', video_directive)

class VideoElement(pyglet.text.document.InlineElement):
    def __init__(self, video_filename, width=None, height=None, loop=False):
        self.video_filename = video_filename

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

        self.width = width is None and self.video_width or width
        self.height = height is None and self.video_height or height

        self.vertex_lists = {}

        super(VideoElement, self).__init__(self.height, 0, self.width)

    def on_enter(self, viewport_width, viewport_height):
        self.video = pyglet.resource.media(self.video_filename)

        # create the player
        self.player = pyglet.media.Player()
        self.player.queue(self.video)
        if self.loop:
            self.player.eos_action = self.player.EOS_LOOP
        else:
            self.player.eos_action = self.player.EOS_PAUSE
        self.player.play()

    def on_leave(self):
        self.player.next()
        self.player = None
        self.video = None
        self.texture = None

    def place(self, layout, x, y):
        texture = self.player.texture
        # set up rendering the player texture
        x1 = int(x)
        y1 = int(y + self.descent)
        x2 = int(x + self.width)
        y2 = int(y + self.height + self.descent)
        group = pyglet.graphics.TextureGroup(texture, layout.top_group)
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('c3B', (255, 255, 255) * 4),
            ('t3f', texture.tex_coords))
        self.vertex_lists[layout] = vertex_list

    def remove(self, layout):
        if layout in self.vertex_lists:
            self.vertex_lists[layout].delete()
            del self.vertex_lists[layout]

