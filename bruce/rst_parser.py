import docutils.parsers.rst
from docutils.core import publish_doctree
from docutils import nodes
from docutils.transforms import references

from bruce import page
from bruce.decoration import Decoration

import pyglet
from pyglet.text.formats import structured

def bullet_generator(bullets = u'\u25cf\u25cb\u25a1'):
    i = -1
    while 1:
        i = (i + 1)%3
        yield bullets[i]
bullet_generator = bullet_generator()

default_stylesheet = dict(
    default = dict(
        font_name='Arial',
        font_size=20,
        margin_bottom=12,
        align='left',
    ),
    emphasis = dict(
        italic=True,
    ),
    strong = dict(
        bold=True,
    ),
    literal = dict(
        font_name='Courier New',
    ),
    literal_block = dict(
        font_name='Courier New',
        font_size=20,
        margin_left=20,
    ),
    layout = dict(
        valign='top',
    ),
    decoration = Decoration(''),
)

def copy_stylesheet(d):
    new = {}
    for k in d:
        new[k] = d[k].copy()
    return new

boolean_true = set('yes true on'.split())

style_types = dict(
    font_size = int,
    margin_left = int, margin_right = int, margin_top = int, margin_bottom = int,
    bold = lambda v: v.lower() in boolean_true, italic = lambda v: v.lower() in boolean_true,
    valign = str, align = str, font_name = unicode,
)

class Section(object):
    def __init__(self, level):
        self.level = level

class DocutilsDecoder(structured.StructuredTextDecoder):
    def __init__(self, stylesheet=None):
        super(DocutilsDecoder, self).__init__()
        if not stylesheet:
            stylesheet = dict(default_stylesheet)
        self.stylesheet = stylesheet
        self.pages = []
        self.document = None

    def decode_structured(self, text, location):
        self.location = location
        if isinstance(location, pyglet.resource.FileLocation):
            doctree = publish_doctree(text, source_path=location.path)
        else:
            doctree = publish_doctree(text)
        doctree.walkabout(DocutilsVisitor(doctree, self))

    def depart_unknown(self, node):
        pass

    def prune(self):
        raise docutils.nodes.SkipNode


    #
    # Page construction
    #
    def new_page(self, node):
        self.push_style(node, self.stylesheet['default'])
        self.in_literal = False
        self.document = pyglet.text.document.FormattedDocument()
        self.stylesheet['decoration'].title = None
        self.len_text = 0
        self.first_paragraph = True
        self.next_style = dict(self.current_style)
        self.notes = []

    def finish_page(self):
        if self.len_text:
            p = TextPage(self.document, copy_stylesheet(self.stylesheet))
            self.pages.append(p)
        self.document = None
        self.len_text = 0


    #
    # Structural elements
    #
    def visit_document(self, node):
        self.new_page(node)

    def depart_document(self, node):
        self.finish_page()

    def visit_title(self, node):
        # title is handled separately so it may be placed nicely
        self.stylesheet['decoration'].title = node.children[0].astext().replace('\n', ' ')
        self.prune()

    def visit_section(self, node):
        # finish off a prior non-section page
        self.finish_page()
        self.new_page(node)

    def depart_section(self, node):
        self.finish_page()

    def visit_transition(self, node):
        self.finish_page()
        self.new_page(node)

    def visit_substitution_definition(self, node):
        self.prune()

    def visit_system_message(self, node):
        self.prune()


    #
    # Body elements
    #
    def visit_Text(self, node):
        text = node.astext()
        if self.in_literal:
            text = text.replace('\n', u'\u2028')
        else:
            # collapse newlines to reintegrate para
            text = text.replace('\n', ' ')
        self.add_text(text)

    def break_paragraph(self):
        '''Break the previous paragraphish.
        '''
        if self.first_paragraph:
            self.first_paragraph = False
            return
        self.add_text('\n')

    paragraph_suppress_newline = False
    def visit_paragraph(self, node):
        if not self.paragraph_suppress_newline:
            self.break_paragraph()
            if self.in_item:
                self.add_text('\t')
        self.paragraph_suppress_newline = False

    def visit_literal_block(self, node):
        self.break_paragraph()
        self.push_style(node, self.stylesheet['literal_block'])
        self.in_literal = True

    def depart_literal_block(self, node):
        self.in_literal = False

    def visit_image(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()
        image = pyglet.image.load(node['uri'])
        # XXX handle dimensions
        self.add_element(structured.ImageElement(image))

    def visit_bullet_list(self, node):
        l = structured.UnorderedListBuilder(bullet_generator.next())
        style = {}
        l.begin(self, style)
        self.push_style(node, style)
        self.list_stack.append(l)
    def depart_bullet_list(self, node):
        self.list_stack.pop()

    def visit_enumerated_list(self, node):
        # XXX node.prefix
        format = {
            'arabic': '1',
            'lowerroman': 'i',
            'upperroman': 'I',
        }[node['enumtype']] + node['suffix']
        l = structured.OrderedListBuilder(1, format)
        style = {}
        l.begin(self, style)
        self.push_style(node, style)
        self.list_stack.append(l)
    def depart_enumerated_list(self, node):
        self.list_stack.pop()

    in_item = False
    def visit_list_item(self, node):
        self.break_paragraph()
        self.list_stack[-1].item(self, {})
        self.paragraph_suppress_newline = True
        # indicate that new paragraphs need to be indented
        self.in_item = True
    def depart_list_item(self, node):
        self.in_item = False

    def visit_note(self, node):
        self.notes.append(node.children[0].astext().replace('\n', ' '))
        self.prune()


    #
    # Inline elements
    #
    def visit_emphasis(self, node):
        self.push_style(node, self.stylesheet['emphasis'])

    def visit_strong(self, node):
        self.push_style(node, self.stylesheet['strong'])
        
    def visit_literal(self, node):
        self.push_style(node, self.stylesheet['literal'])

    def visit_superscript(self, node):
        self.push_style(node, self.stylesheet['superscript'])

    def visit_subscript(self, node):
        self.push_style(node, self.stylesheet['subscript'])


    #
    # style element
    #
    def visit_style(self, node):
        for line in node.get_style().splitlines():
            key, value = line.strip().split('=')
            if '.' in key:
                group, key = key.split('.')
                value = style_types[key](value)
            else:
                group = 'default'
                value = style_types[key](value)
                self.push_style('style-element', {key: value})
            self.stylesheet[group][key] = value

    def visit_video(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()
        # XXX handle dimensions
        self.add_element(VideoElement(node.get_video()))

    def visit_decoration(self, node):
        self.stylesheet['decoration'].content = node.get_decoration()

#
# Style directive
#
class style(nodes.Special, nodes.Invisible, nodes.Element):
    def get_style(self):
        return self.rawsource

def style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ style('\n'.join(content)) ]
style_directive.arguments = (0, 0, 0)
style_directive.content = True
docutils.parsers.rst.directives.register_directive('style', style_directive)

#
# Decoration directive
#
class decoration(nodes.Special, nodes.Invisible, nodes.Element):
    def get_decoration(self):
        return self.rawsource

def decoration_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ decoration('\n'.join(content)) ]
decoration_directive.arguments = (0, 0, 0)
decoration_directive.content = True
docutils.parsers.rst.directives.register_directive('decoration', decoration_directive)


#
# Video directive
#
class video(nodes.Special, nodes.Invisible, nodes.Element):
    def get_video(self):
        return self.rawsource

def video_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ video('\n'.join(content)) ]
video_directive.arguments = (0, 0, 0)
video_directive.content = True
docutils.parsers.rst.directives.register_directive('video', video_directive)

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
        x1 = x
        y1 = y + self.descent
        x2 = x + self.width
        y2 = y + self.height + self.descent
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


class DocutilsVisitor(nodes.NodeVisitor):
    def __init__(self, document, decoder):
        nodes.NodeVisitor.__init__(self, document)
        self.decoder = decoder

    def dispatch_visit(self, node):
        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'visit_%s' % node_name)
        #, self.decoder.visit_unknown)
        method(node)

    def dispatch_departure(self, node):
        self.decoder.pop_style(node)

        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'depart_%s' % node_name,
                         self.decoder.depart_unknown)
        method(node)


class TextPage(page.Page):
    name = 'rst-text'
    def __init__(self, document, stylesheet):
        self.document = document
        self.stylesheet = stylesheet
        self.decoration = stylesheet['decoration']

    def layout(self, x, y, vw, vh):
        self.batch = pyglet.graphics.Batch()

        # render the text lines to our batch
        l = self._layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, vw, vh, multiline=True, batch=self.batch)

        # do alignment
        l.begin_update()
        l.valign = self.stylesheet['layout']['valign']
        if l.valign == 'center': l.y = y + vh//2
        elif l.valign == 'top': l.y = y + vh
        else: l.y = y
        #l.halign = self.stylesheet['layout']['halign']
        #if l.halign == 'center': l.x = x + vw//2
        #elif l.halign == 'right': l.x = x + vw
        #else: l.x = x
        l.end_update()

    def cleanup(self):
        self._layout.delete()
        self._layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

def parse(text, html=False):
    assert not html, 'use rst2html for html!'

    # everything is UTF-8, suckers
    text = text.decode('utf8')

    d = DocutilsDecoder()
    d.decode(text)
    return d.pages

__all__ = ['parse']

