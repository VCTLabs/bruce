import os

import docutils.parsers.rst
from docutils.core import publish_doctree
from docutils import nodes
from docutils.transforms import references

import pyglet
from pyglet.text.formats import structured

# these imports simply cause directives to be registered
from bruce import decoration
from bruce import resource
from bruce.page import Page

from bruce.style import *
from bruce.video import VideoElement

def bullet_generator(bullets = u'\u25cf\u25cb\u25a1'):
    i = -1
    while 1:
        i = (i + 1)%3
        yield bullets[i]
bullet_generator = bullet_generator()

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
            p = Page(self.document, copy_stylesheet(self.stylesheet))
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
        # push both the literal (character style) and literal_block (block
        # style)... the use of "dummy" will ensure both are popped off when
        # we exit the block
        self.push_style(node, self.stylesheet['literal'])
        self.push_style('dummy', self.stylesheet['literal_block'])
        self.in_literal = True

    def depart_literal_block(self, node):
        self.in_literal = False

    def visit_image(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()
        image = pyglet.image.load(node['uri'].strip())

        # XXX allow image to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if node.has_key('width'):
            kw['width'] = int(node['width'])
        if node.has_key('height'):
            kw['height'] = int(node['height'])
            if 'width' not in kw:
                scale = kw['height'] / float(image.height)
                kw['width'] = int(scale * image.width)
        elif 'width' in kw:
            scale = kw['width'] / float(image.width)
            kw['height'] = int(scale * image.height)

        self.add_element(structured.ImageElement(image, **kw))

    def visit_video(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        # XXX allow image to fill the available layout dimensions

        # handle width and height, retaining aspect if only one is specified
        kw = {}
        if node.has_key('width'):
            kw['width'] = int(node['width'])
        if node.has_key('height'):
            kw['height'] = int(node['height'])
        self.add_element(VideoElement(node.get_video(), **kw))

    def visit_bullet_list(self, node):
        l = structured.UnorderedListBuilder(bullet_generator.next())
        style = {}
        l.begin(self, style)
        self.push_style(node, style)
        self.list_stack.append(l)
    def depart_bullet_list(self, node):
        self.list_stack.pop()

    def visit_enumerated_list(self, node):
        format = node['prefix'] + {
            'arabic': '1',
            'lowerroman': 'i',
            'upperroman': 'I',
            'loweralpha': 'a',
            'upperalpha': 'A',
        }[node['enumtype']] + node['suffix']
        start = int(node.get('start', 1))
        l = structured.OrderedListBuilder(start, format)
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
    # Style and decoration
    #
    def visit_style(self, node):
        for key, value in node.attlist():
            if '.' in key:
                group, key = key.split('.')
            else:
                group = 'default'
                self.push_style('style-element', {key: value})
            self.stylesheet[group][key] = value

    def visit_decoration(self, node):
        self.stylesheet['decoration'].content = node.get_decoration()


    #
    # Resource location
    #
    def visit_resource(self, node):
        resource_name = node.get_resource()
        # XXX
        #if not os.path.isabs(resource_name):
            #resource_name = os.path.join(config.get('directory'), line)
        if resource_name.lower().endswith('.ttf'):
            pyglet.resource.add_font(resource_name)
        else:
            pyglet.resource.path.append(resource_name)
        pyglet.resource.reindex()

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


def parse(text, html=False):
    assert not html, 'use rst2html for html!'

    # everything is UTF-8, suckers
    text = text.decode('utf8')

    d = DocutilsDecoder()
    d.decode(text)
    return d.pages

__all__ = ['parse']
