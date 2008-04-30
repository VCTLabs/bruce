import docutils.parsers.rst
from docutils.core import publish_doctree
from docutils import nodes

from bruce import page

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
        margin_bottom=12
    ),
    emphasis = dict(
        italic=True
    ),
    strong = dict(
        bold=True
    ),
    literal = dict(
        font_name='Courier New'
    ),
    literal_block = dict(
        font_name='Courier New',
        font_size=20,
        margin_left=20,
    ),
    title = dict(
        font_size=28,
        bold=True,
        align='center'
    ),
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

    def decode_structured(self, text, location):
        self.location = location
        if isinstance(location, pyglet.resource.FileLocation):
            doctree = publish_doctree(text, source_path=location.path)
        else:
            doctree = publish_doctree(text)
        doctree.walkabout(DocutilsVisitor(doctree, self))

    def visit_Text(self, node):
        text = node.astext()
        if self.in_literal:
            text = text.replace('\n', u'\u2028')
        self.add_text(text)

    def visit_unknown(self, node):
        pass

    def depart_unknown(self, node):
        pass

    # Structural elements

    def visit_title(self, node):
        self.push_style(node, self.stylesheet['title'])

    def depart_title(self, node):
        self.add_text('\n')

    def visit_section(self, node):
        self.push_style(node, self.stylesheet['default'])
        self.in_literal = False
        self.document = pyglet.text.document.FormattedDocument()
        self.len_text = 0
        self.next_style = dict(self.current_style)

    def depart_section(self, node):
        p = RstTextPage('', 0, 0, '', document=self.document,
            bgcolor='255,255,255,255')
        self.pages.append(p)

    # Body elements

    def depart_paragraph(self, node):
        self.add_text('\n')

    def visit_literal_block(self, node):
        self.push_style(node, self.stylesheet['literal_block'])
        self.in_literal = True

    def depart_literal_block(self, node):
        self.in_literal = False
        self.add_text('\n')

    def visit_image(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        #if isinstance(node.parent, nodes.Structural):
        #    self.add_text('\n')
        image = pyglet.image.load(node['uri'])
        self.add_element(structured.ImageElement(image))

    def visit_bullet_list(self, node):
        l = structured.UnorderedListBuilder(bullet_generator.next())
        l.begin(self, {})
        self.list_stack.append(l)
    def depart_bullet_list(self, node):
        self.list_stack.pop()
        self.add_text('\n')

    def visit_enumerated_list(self, node):
        # XXX node.prefix
        format = {
            'arabic': '1',
            'lowerroman': 'i',
            'upperroman': 'I',
        }[node['enumtype']] + node['suffix']
        l = structured.OrderedListBuilder(1, format)
        l.begin(self, {})
        self.list_stack.append(l)
    def depart_enumerated_list(self, node):
        self.list_stack.pop()
        self.add_text('\n')

    def visit_list_item(self, node):
        self.list_stack[-1].item(self, {})
    def depart_list_item(self, node):
        pass

    # Inline elements
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

    # Config
    def visit_config(self, node):
        for line in node.get_config().splitlines():
            key,value = line.strip().split('=')
            group, key = key.split('.')
            if key == 'font_name': value=str(value)
            self.stylesheet[group][key] = value
    def depart_config(self, node):
        pass

class config(nodes.Special, nodes.Invisible, nodes.Element):
    def get_config(self):
        return self.rawsource

def config_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ config('\n'.join(content)) ]
config_directive.arguments = (0, 0, 0)
config_directive.content = True
docutils.parsers.rst.directives.register_directive('config', config_directive)


class DocutilsVisitor(nodes.NodeVisitor):
    def __init__(self, document, decoder):
        nodes.NodeVisitor.__init__(self, document)
        self.decoder = decoder

    def dispatch_visit(self, node):
        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'visit_%s' % node_name,
                         self.decoder.visit_unknown)
        method(node)

    def dispatch_departure(self, node):
        self.decoder.pop_style(node)

        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'depart_%s' % node_name, 
                         self.decoder.depart_unknown)
        method(node)


class RstTextPage(page.Page):
    name = 'rst-text'
    def __init__(self, *args, **kw):
        self.document = kw.pop('document')
        self.decorations = []
        super(RstTextPage, self).__init__(*args, **kw)

    def on_enter(self, vw, vh):
        super(RstTextPage, self).on_enter(vw, vh)

        self.batch = pyglet.graphics.Batch()

        self.decorations.append(self.batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v2i', (0, vh-50, vw, vh-50, vw, vh, 0, vh)),
            ('c3B', (200, 200, 100)*4),
        ))
        self.decorations.append(self.batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v2i', (0, 0, vw, 0, vw, 50, 0, 50)),
            ('c3B', (200, 200, 100)*4),
        ))

        # render the text lines to our batch
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.begin_update()
        self.layout.valign = 'top'
        self.layout.y = vh
        self.layout.end_update()

    def on_leave(self):
        for decoration in self.decorations:
            decoration.delete()
        self.decorations = []
        self.layout.delete()
        self.layout = None
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

