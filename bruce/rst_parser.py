'''

Ideas

Presentation has decorations layer in background.

Pages may specify no decoration.

Pages may specify no title. Though pages with no title are pretty ugly thanks to
the now-unnecessary title. Perhaps ReST just isn't suited to that kind of presentation?

Or perhaps I can have page directives which are structural like Sections?

Pages may specify arguments to layout: halign and valign


Layout.valign/halign are actually *anchors*.


'''


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
    layout = dict(
        valign='top',
        halign='left'
    ),
    decoration = Decoration(''),
)

boolean_true = set('yes true on'.split())

style_types = dict(
    font_size = int,
    margin_left = int, margin_right = int, margin_top = int, margin_bottom = int,
    bold = lambda v: v.lower() in boolean_true, italic = lambda v: v.lower() in boolean_true,
    valign = str, halign = str, font_name = unicode,
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

    def visit_document(self, node):
        # XXX maybe something here of interest?
        pass

    #def visit_unknown(self, node):
        #pass

    def depart_unknown(self, node):
        pass

    def visit_Text(self, node):
        if self.document is None:
            print 'WARNING: text outside Section', node
            return
        text = node.astext()
        if self.in_literal:
            text = text.replace('\n', u'\u2028')
        else:
            # collapse newlines to reintegrate para
            text = text.replace('\n', ' ')
        self.add_text(text)


    # Structural elements

    def visit_title(self, node):
        self.break_paragraph()
        self.push_style(node, self.stylesheet['title'])

    def visit_section(self, node):
        self.push_style(node, self.stylesheet['default'])
        self.in_literal = False
        self.document = pyglet.text.document.FormattedDocument()
        self.len_text = 0
        self.first_paragraph = True
        self.next_style = dict(self.current_style)

    def depart_section(self, node):
        p = TextPage(self.document, self.stylesheet)
        self.pages.append(p)

    def visit_transition(self, node):
        self.depart_section(node)
        self.visit_section(node)

    def prune(self, node):
        raise docutils.nodes.SkipNode

    def visit_substitution_definition(self, node):
        self.prune(node)

    def visit_system_message(self, node):
        self.prune(node)

    # Body elements

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


    # style element

    def visit_style(self, node):
        for line in node.get_style().splitlines():
            key,value = line.strip().split('=')
            group, key = key.split('.')
            value = style_types[key](value)
            self.stylesheet[group][key] = value

    def visit_decoration(self, node):
        content = []
        args = {}
        for line in node.get_decoration().splitlines():
            if ':' in line:
                content.append(line)
            else:
                key, value = line.strip().split('=')
                args[str(key)] = style_types[key](value)
        self.stylesheet['decoration'] = Decoration('\n'.join(content), **args)

class style(nodes.Special, nodes.Invisible, nodes.Element):
    def get_style(self):
        return self.rawsource

def style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ style('\n'.join(content)) ]
style_directive.arguments = (0, 0, 0)
style_directive.content = True
docutils.parsers.rst.directives.register_directive('style', style_directive)

class decoration(nodes.Special, nodes.Invisible, nodes.Element):
    def get_decoration(self):
        return self.rawsource

def decoration_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ decoration('\n'.join(content)) ]
decoration_directive.arguments = (0, 0, 0)
decoration_directive.content = True
docutils.parsers.rst.directives.register_directive('decoration', decoration_directive)


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

    def on_enter(self, vw, vh):
        super(TextPage, self).on_enter(vw, vh)

        self.batch = pyglet.graphics.Batch()

        # render the text lines to our batch
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.begin_update()
        print self.stylesheet['layout']
        if self.stylesheet['layout']['valign'] == 'center':
            self.layout.valign = 'center'
            self.layout.y = vh//2
        elif self.stylesheet['layout']['valign'] == 'top':
            self.layout.valign = 'top'
            self.layout.y = vh
        else:
            self.layout.valign = 'bottom'
            self.layout.y = 0
        self.layout.end_update()

    def on_leave(self):
        super(TextPage, self).on_leave()
        self.layout.delete()
        self.layout = None
        self.batch = None

    def draw(self):
        self.decoration.draw()
        self.batch.draw()

def parse(text, html=False):
    assert not html, 'use rst2html for html!'

    # everything is UTF-8, suckers
    text = text.decode('utf8')

    d = DocutilsDecoder()
    d.decode(text)
    return d.pages

__all__ = ['parse']
