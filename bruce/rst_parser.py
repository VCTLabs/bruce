import os

import docutils.parsers.rst
from docutils.core import publish_doctree
from docutils import nodes
from docutils.transforms import references, Transform

import pyglet
from pyglet.text.formats import structured

# these imports simply cause directives to be registered
from bruce import decoration
from bruce import interpreter, video
from bruce import resource
from bruce.image import ImageElement

# the basic page
from bruce.page import Page

from bruce.style import *

def bullet_generator(bullets = u'\u25cf\u25cb\u25a1'):
    i = -1
    while 1:
        i = (i + 1)%3
        yield bullets[i]
bullet_generator = bullet_generator()

class Section(object):
    def __init__(self, level):
        self.level = level

class SectionContent(Transform):
    """
    Ensure all content resides in a section. Top-level content
    may be split by transitions into multiple sections.

    For example, transform this::

        content
        <transition>
        content
        <section>

    into this::

        <section>
        <section>
        <section>
    """
    def apply(self):
        self.current = []
        index = 0
        for node in list(self.document):
            if isinstance(node, nodes.transition):
                self.document.remove(node)
                if self.current:
                    new = nodes.section()
                    new.children = self.current
                    self.document.insert(index, new)
                    self.current = []
                    index += 1
            elif isinstance(node, nodes.section):
                if self.current:
                    new = nodes.section()
                    new.children = self.current
                    self.document.insert(index, new)
                    self.current = []
                index += 1
            else:
                self.current.append(node)
                self.document.remove(node)

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

        # transform to allow top-level transitions to create sections
        SectionContent(doctree).apply()

        doctree.walkabout(DocutilsVisitor(doctree, self))

    def depart_unknown(self, node):
        pass

    #
    # Structural elements
    #
    def visit_document(self, node):
        pass

    def visit_section(self, node):
        '''Add a page
        '''
        g = DocumentGenerator(self.stylesheet)
        d = g.decode(node)
        if g.len_text:
            p = Page(d, copy_stylesheet(self.stylesheet), d.elements)
            self.pages.append(p)
        raise docutils.nodes.SkipNode

class DummyReporter(object):
    debug = lambda *args: None

class DocumentGenerator(structured.StructuredTextDecoder):
    def __init__(self, stylesheet):
        super(DocumentGenerator, self).__init__()
        self.stylesheet = stylesheet

    def decode_structured(self, doctree, location):
        # attach a reporter so docutil's walkabout doesn't get confused by us
        # not using a real document as the root
        doctree.reporter = DummyReporter()

        # initialise parser
        self.push_style(doctree, self.stylesheet['default'])
        self.in_literal = False
        self.stylesheet['decoration'].title = None
        self.first_paragraph = True
        self.next_style = dict(self.current_style)
        self.notes = []
        self.elements = self.document.elements = []

        # go walk the doc tree
        visitor = DocutilsVisitor(doctree, self)
        children = doctree.children
        try:
            for child in children[:]:
                child.walkabout(visitor)
        except nodes.SkipSiblings:
            pass

    def depart_unknown(self, node):
        pass

    def prune(self):
        raise docutils.nodes.SkipNode

    def add_element(self, element):
        self.elements.append(element)
        super(DocutilsDecoder, self).add_element(element)

    def visit_title(self, node):
        # title is handled separately so it may be placed nicely
        self.stylesheet['decoration'].title = node.children[0].astext().replace('\n', ' ')
        self.prune()

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
        if not (isinstance(node.parent, nodes.TextElement) or
                isinstance(node.parent, nodes.Part)):
            self.break_paragraph()
        kw = {}
        if node.has_key('width'):
            kw['width'] = int(node['width'])
        if node.has_key('height'):
            kw['height'] = int(node['height'])
        self.add_element(ImageElement(node['uri'].strip(), **kw))

    def visit_video(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        self.add_element(node.get_video())

    def visit_interpreter(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        self.add_element(node.get_interpreter())

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

    def visit_definition_list(self, node):
        pass
    def visit_definition_list_item(self, node):
        self.break_paragraph()
    def visit_term(self, node):
        pass
    def visit_definition(self, node):
        style = {}
        left_margin = self.current_style.get('margin_left') or 0
        tab_stops = self.current_style.get('tab_stops')
        if tab_stops:
            tab_stops = list(tab_stops)
        else:
            tab_stops = []
        tab_stops.append(left_margin + 50)
        style['margin_left'] = left_margin + 50
        style['indent'] = -30
        style['tab_stops'] = tab_stops
        self.push_style(node, style)
        self.in_item = True
    def depart_definition(self, node):
        self.in_item = False

    def visit_block_quote(self, node):
        style = self.stylesheet['default'].copy()
        left_margin = self.current_style.get('margin_left') or 0
        tab_stops = self.current_style.get('tab_stops')
        if tab_stops:
            tab_stops = list(tab_stops)
        else:
            tab_stops = []
        tab_stops.append(left_margin + 50)
        style['margin_left'] = left_margin + 50
        style['indent'] = -30
        style['tab_stops'] = tab_stops
        self.push_style(node, style)
        self.in_item = True
    def depart_block_quote(self, node):
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
        if hasattr(node, 'get_decoration'):
            self.stylesheet['decoration'].content = node.get_decoration()
        else:
            # it's probably a footer or something
            pass

    def visit_footer(self, node):
        g = DocumentGenerator(self.stylesheet, node)
        self.stylesheet['decoration'].footer = g.parse()

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

