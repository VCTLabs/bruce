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

        content1
        <transition>
        content2
        <section>
        content3
        <transition>
        content4

    into this::

        <section content1>
        <section content2>
        <section content3>
        <section content4>
    """
    def apply(self):
        new_section_content = []
        index = 0
        def add_section():
            new = nodes.section()
            new.children = list(new_section_content)
            self.document.insert(index, new)
            new_section_content[:] = []
        record_for_later = True
        for node in list(self.document):
            if isinstance(node, nodes.transition):
                self.document.remove(node)
                if new_section_content:
                    add_section()
                    index += 1

                record_for_later = True
            elif isinstance(node, nodes.section):
                if new_section_content:
                    # add accumulated content
                    add_section()
                    index += 1

                # and acknowledge the section
                index += 1
                record_for_later = False

                # grab any transition-delimited pages from the section
                move_from_section = False
                for n, child in enumerate(list(node.children)):
                    new_section_content[:] = []
                    if isinstance(child, nodes.transition):
                        move_from_section = True
                        node.remove(child)
                        if new_section_content:
                            add_section()
                            index += 1
                    else:
                        if move_from_section:
                            new_section_content.append(child)
                            node.remove(child)
            elif record_for_later:
                new_section_content.append(node)
                self.document.remove(node)
        if new_section_content:
            add_section()

def printtree(node, indent=''):
    if hasattr(node, 'children') and node.children:
        print indent + '<%s>'%node.__class__.__name__
        for child in node.children:
            printtree(child, indent+'  ')
        print indent + '</%s>'%node.__class__.__name__
    else:
        print indent + repr(node)


class DocutilsDecoder(structured.StructuredTextDecoder):
    def __init__(self, stylesheet=None):
        super(DocutilsDecoder, self).__init__()
        if not stylesheet:
            stylesheet = default_stylesheet.copy()
        self.stylesheet = stylesheet
        self.decoration = decoration.Decoration('', stylesheet)
        self.pages = []
        self.document = None

    def decode_structured(self, text, location):
        self.location = location
        if isinstance(location, pyglet.resource.FileLocation):
            doctree = publish_doctree(text, source_path=location.path)
        else:
            doctree = publish_doctree(text)

        # transform to allow top-level transitions to create sections
        #printtree(doctree)
        SectionContent(doctree).apply()
        #printtree(doctree)

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
        self.decoration.title = None
        g = DocumentGenerator(self.stylesheet, self.decoration)
        d = g.decode(node)
        if g.len_text:
            p = Page(d, self.stylesheet.copy(), self.decoration.copy(),
                d.elements, node)
            self.pages.append(p)
        raise docutils.nodes.SkipNode

class DummyReporter(object):
    debug = lambda *args: None

class DocumentGenerator(structured.StructuredTextDecoder):
    def __init__(self, stylesheet, decoration, style_base_class='default'):
        super(DocumentGenerator, self).__init__()
        self.stylesheet = stylesheet
        self.decoration = decoration
        self.style_base_class = style_base_class

    def decode_structured(self, doctree, location):
        # attach a reporter so docutil's walkabout doesn't get confused by us
        # not using a real document as the root
        doctree.reporter = DummyReporter()

        # initialise parser
        self.push_style(doctree, self.stylesheet[self.style_base_class])
        self.in_literal = False
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
        super(DocumentGenerator, self).add_element(element)

    def visit_title(self, node):
        # title is handled separately so it may be placed nicely
        self.decoration.title = node.children[0].astext().replace('\n', ' ')
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
        if self.in_item:
            self.add_text('\t')

    paragraph_suppress_newline = False
    def visit_paragraph(self, node):
        if not self.paragraph_suppress_newline:
            self.break_paragraph()
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

    # Line blocks have lines in them, we just have to add a hard-return to the
    # lines. Line blocks should only indent child blocks.
    line_block_count = 0
    def visit_line_block(self, node):
        if self.line_block_count:
            self.push_style(node, self.stylesheet['line_block'])
        else:
            self.break_paragraph()
        self.line_block_count += 1
    def visit_line(self, node):
        pass
    def depart_line(self, node):
        self.add_text(u'\u2028')
    def depart_line_block(self, node):
        self.line_block_count -= 1

    def visit_image(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if (not isinstance(node.parent, nodes.TextElement)
                and not self.paragraph_suppress_newline):
            self.break_paragraph()
        self.paragraph_suppress_newline = False
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
        pass
    def visit_term(self, node):
        self.break_paragraph()
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
        style = self.stylesheet[self.style_base_class].copy()
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
    def visit_load_style(self, node):
        self.stylesheet.update(node.get_style())
        self.stack = []
        self.push_style('default', self.stylesheet['default'])
        self.next_style = dict(self.current_style)

    def visit_style(self, node):
        # XXX detect changes in footer style
        for key, value in node.attlist():
            if '.' in key:
                group, key = key.split('.')
            else:
                group = 'default'
                self.push_style('style-element', {key: value})
            self.stylesheet[group][key] = value

    def visit_decoration(self, node):
        # make sure it's Bruce's decoration node, otherwise it's probably a
        # footer or something
        if hasattr(node, 'get_decoration'):
            self.decoration.content = node.get_decoration()

    def visit_footer(self, node):
        # XXX stop footer from being coalesced into one element!
        g = DocumentGenerator(self.stylesheet, None, style_base_class='footer')
        self.decoration.footer = g.decode(node)
        self.prune()

    #
    # Resource location
    #
    def visit_resource(self, node):
        resource_name = node.get_resource()
        if resource_name.lower().endswith('.ttf'):
            pyglet.resource.add_font(resource_name)
        elif not os.path.isabs(resource_name):
            # try to find the resource inside an existing resource directory
            for path in pyglet.resource.path:
                if not os.path.isdir(path): continue
                p = os.path.join(path, resource_name)
                if os.path.exists(p):
                    pyglet.resource.path.append(p)
                    break
            else:
                raise ValueError('Resource %s not found'%resource_name)
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

