from docutils import nodes
from docutils.parsers.rst import directives

import pyglet

#
# Video directive
#
class video(nodes.Special, nodes.Invisible, nodes.Element):
    def get_video(self):
        return self.rawsource

def video_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ video('\n'.join(arguments), **options) ]
video_directive.arguments = (1, 0, 1)
video_directive.options = dict(
     width=directives.positive_int,
     height=directives.positive_int,
)
video_directive.content = True
directives.register_directive('video', video_directive)

class VideoElement(pyglet.text.document.InlineElement):
    def __init__(self, video_filename, width=None, height=None, loop=False):
        self.video_filename = video_filename

        video = pyglet.media.load(self.video_filename)

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

        self.width = width is None and self.video_width or width
        self.height = height is None and self.video_height or height

        self.vertex_lists = {}

        ascent = max(0, self.height)
        descent = 0 #min(0, -anchor_y)
        super(VideoElement, self).__init__(ascent, descent, self.width)

    def place(self, layout, x, y):
        self.video = pyglet.media.load(self.video_filename)
        # create the player
        self.player = pyglet.media.Player()
        self.player.queue(self.video)
        if self.loop:
            self.player.eos_action = self.player.EOS_LOOP
        else:
            self.player.eos_action = self.player.EOS_PAUSE
        self.player.play()

        # set up rendering the player texture
        texture = self.player.texture
        group = pyglet.graphics.TextureGroup(texture, layout.top_group)
        x1 = int(x)
        y1 = int(y + self.descent)
        x2 = int(x + self.width)
        y2 = int(y + self.height + self.descent)
        vertex_list = layout.batch.add(4, pyglet.gl.GL_QUADS, group,
            ('v2i', (x1, y1, x2, y1, x2, y2, x1, y2)),
            ('c3B', (255, 255, 255) * 4),
            ('t3f', texture.tex_coords))
        self.vertex_lists[layout] = vertex_list

    vertex_list = None
    def remove(self, layout):
        self.player.next()
        self.player = None
        self.layout = None
        if self.vertex_list:
            self.vertex_list.delete()
        self.vertex_list = None

