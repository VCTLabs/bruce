import os
import re
import warnings

import docutils.parsers.rst
from docutils.core import publish_doctree
from docutils import nodes
from docutils.transforms import references, Transform

import pyglet
from pyglet.text.formats import structured

try:
    import smartypants
    def curlify(text):
        """Replace quotes in `text` with curly equivalents."""
        if config.options.smartypants == 'off':
            return text
        # Replace any ampersands with an entity so we don't harm the text.
        text = text.replace('&', '&#38;')
        # Use smartypants to curl the quotes, creating HTML entities
        text = smartypants.smartyPants(text, config.options.smartypants)
        # Replace the entities with real Unicode characters.
        text = re.sub('&#(\d+);', lambda m: unichr(int(m.group(1))), text)
        return text
except ImportError:
    # No smartypants: no curly quotes for you!
    def curlify(text):
        return text

from bruce import page
from bruce import pygments_parser
from bruce import config
from bruce.image import ImageElement

# custom reST directives
from bruce import layout; layout.register_directives()
from bruce import interpreter; interpreter.register_directives()
from bruce import video; video.register_directives()
from bruce import plugin; plugin.register_directives()
from bruce import code_block; code_block.register_directives()
from bruce import blank; blank.register_directives()
from bruce import resource; resource.register_directives()
from bruce import style; style.register_directives()

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
        decoration = None
        for node in list(self.document):
            if isinstance(node, nodes.decoration):
                decoration = node
                self.document.remove(node)

            elif isinstance(node, nodes.transition):
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
                new_section_content[:] = []
                for n, child in enumerate(list(node.children)):
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

        if decoration is not None:
            self.document.append(decoration)

class BulletSections(Transform):
    """
    Split up the top-level bullet list(s) found in section(s) and
    a new section for each bullet point.

    For example, transform this::


        <document>
         <section>
          <bullet_list>
           <list_item>content1</list_item>
           <list_item>content2</list_item>
           <list_item>content3</list_item>
           <list_item>content4</list_item>
          </bullet_list>
         </section>
        </document>

    into this::

        <document>
         <section>content1</section>
         <section>content2</section>
         <section>content3</section>
         <section>content4</section>
        </document>

    Note: **only transforms the first section**
    """
    def apply(self):
        for section in self.document:
            if isinstance(section, nodes.section):
                break
        else:
            # there is no section content - presentation is empty!
            return

        self.document.remove(section)

        for node in section:
            if isinstance(node, nodes.bullet_list):
                for n, child in enumerate(node):
                    new = nodes.section()
                    new.children = list(child.children)
                    self.document.insert(n, new)
            else:
                warnings.warn('Unexpected top-level %s'%node.__class__.__name__)

def printtree(node, indent=''):
    if hasattr(node, 'children') and node.children:
        print indent + '<%s>'%node.__class__.__name__
        for child in node.children:
            printtree(child, indent+'  ')
        print indent + '</%s>'%node.__class__.__name__
    else:
        print indent + repr(node)


class DocutilsDecoder(structured.StructuredTextDecoder):
    def __init__(self, stylesheet, bullet_mode):
        super(DocutilsDecoder, self).__init__()
        self.stylesheet = stylesheet
        self.pages = []
        self.document = None
        self.bullet_mode = bullet_mode

    def decode_structured(self, text, location):
        self.location = location
        if isinstance(location, pyglet.resource.FileLocation):
            doctree = publish_doctree(text, source_path=location.path)
        else:
            doctree = publish_doctree(text)

        # transform to allow top-level transitions to create sections
        SectionContent(doctree).apply()

        # split top-level bullet list into sections too?
        if self.bullet_mode:
            #printtree(doctree)
            BulletSections(doctree).apply()
            #printtree(doctree)

        doctree.walkabout(DocutilsVisitor(doctree, self))

    def visit_unknown(self, node):
        warnings.warn('Unhandled document node %s'%node.__class__.__name__)

    def depart_unknown(self, node):
        pass

    #
    # Structural elements
    #
    def visit_document(self, node):
        pass

    def visit_comment(self, node):
        self.prune()

    def visit_section(self, node):
        '''Add a page
        '''
        self.stylesheet['layout'].title = None
        g = DocumentGenerator(self.stylesheet)
        d = g.decode(node)
        if g.len_text or g.is_blank:
            p = page.Page(d, self.stylesheet.copy(), d.elements, node,
                g.expose_text_runs)
            self.pages.append(p)

        self.stylesheet = g.next_stylesheet

        raise docutils.nodes.SkipNode

    def visit_decoration(self, node):
        pass

    def visit_footer(self, node):
        # XXX try to stop footer from being coalesced into one element?
        g = DocumentGenerator(self.stylesheet, style_base_class='footer')
        footer = g.decode(node)
        for p in self.pages:
            p.stylesheet['layout'].footer = footer
        raise docutils.nodes.SkipNode

class DummyReporter(object):
    debug = lambda *args: None

class DocumentGenerator(structured.StructuredTextDecoder):
    def __init__(self, stylesheet, style_base_class='default'):
        super(DocumentGenerator, self).__init__()

        # the stylesheet for the this page
        self.stylesheet = stylesheet

        # the stylesheet for the *next* page
        self.next_stylesheet = stylesheet

        self.style_base_class = style_base_class
        self.is_blank = False
        self.expose_text_runs = []

    def decode_structured(self, doctree, location):
        # attach a reporter so docutil's walkabout doesn't get confused by us
        # not using a real document as the root
        doctree.reporter = DummyReporter()

        # initialise style
        style = self.stylesheet['default'].copy()
        if self.style_base_class != 'default':
            style.update(self.stylesheet[self.style_base_class])
        self.push_style(doctree, style)

        # initialise parser
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

    def visit_unknown(self, node):
        warnings.warn('Unhandled document node %s'%node.__class__.__name__)

    def depart_unknown(self, node):
        pass

    def prune(self):
        raise docutils.nodes.SkipNode

    def add_element(self, element):
        if self.expose_text_runs:
            self.expose_text_runs[-1]['elements'].append(element)
        self.elements.append(element)
        super(DocumentGenerator, self).add_element(element)

    def visit_title(self, node):
        # title is handled separately so it may be placed nicely
        title = node.children[0].astext().replace('\n', ' ')
        title = curlify(title)
        self.stylesheet['layout'].title = title
        self.prune()

    def visit_substitution_definition(self, node):
        self.prune()

    def visit_system_message(self, node):
        self.prune()

    def visit_comment(self, node):
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
            text = curlify(text)
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

    def visit_doctest_block(self, node, lexer_name='pycon'):
        self.visit_literal_block(node)
        if pygments_parser.have_pygments:
            pygments_parser.handle_rst_node(self, node, lexer_name)
            self.prune()

    def depart_doctest_block(self, node):
        self.depart_literal_block(node)

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

    def visit_blank(self, node):
        self.is_blank = True
        self.prune()

    def visit_code(self, node):
        self.visit_literal_block(node)
        if pygments_parser.have_pygments:
            pygments_parser.handle_rst_node(self, node, node['lexer_name'])
        else:
            # no pygments, just display plain
            self.visit_Text(node)
    def depart_code(self, node):
        self.depart_literal_block(node)

    def visit_video(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        self.add_element(node.get_video())

    def visit_interpreter(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if self.paragraph_suppress_newline:
            self.paragraph_suppress_newline = False
        elif not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        self.add_element(node.get_interpreter(self.stylesheet))

    def visit_table(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if self.paragraph_suppress_newline:
            self.paragraph_suppress_newline = False
        elif not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        # avoid circular import
        from bruce import table

        # override default style with table cell style
        stylesheet = self.stylesheet.copy()
        # XXX any more here?
        stylesheet['default']['align'] = stylesheet['table']['cell_align']

        self.add_element(table.TableElement(self.document, stylesheet, node))
        self.prune()

    def visit_plugin(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if not isinstance(node.parent, nodes.TextElement):
            self.break_paragraph()

        self.add_element(node.get_plugin())

    def visit_bullet_list(self, node):
        n = len(self.list_stack)%3
        style = self.stylesheet['list']['bullet']
        if style:
            bullet = style[n]
        else:
            bullet = ''
        l = structured.UnorderedListBuilder(bullet)
        style = {}
        l.begin(self, style)
        self.push_style(node, style)
        self.list_stack.append(l)
        self.in_item = False
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
        self.in_item = False
    def depart_enumerated_list(self, node):
        self.list_stack.pop()

    in_item = False
    item_depth = 0
    def visit_list_item(self, node):
        self.break_paragraph()

        # possibly mark the item contents as a new expose run
        self.item_depth += 1
        self.mark_expose_run(node)

        # place the bullet or number
        self.list_stack[-1].item(self, {})

        # don't insert a newline for the first paragraph of the item
        self.paragraph_suppress_newline = True

        # indicate that new paragraphs need to be indented
        self.in_item = True

    def mark_expose_run(self, node):
        expose = self.stylesheet.value('list', 'expose')
        if self.item_depth != 1 or expose == 'show':
            return
        # yep, we want the contents of this node marked for gradual exposure
        color = self.stylesheet.value('default', 'color')
        self.push_style(node, dict(color=color))
        self.expose_text_runs.append(dict(style=expose, start=self.len_text,
            on=False, elements=[]))

    def close_expose_run(self):
        if self.item_depth != 1 or not self.expose_text_runs:
            return

        # get list of [(start, end, color)] for the document text of the list
        # item contents
        run = self.expose_text_runs[-1]
        iter = self.document.get_style_runs('color')
        run['runs'] = [[s, e, c] for s, e, c in iter.ranges(run['start'],
            self.len_text)]

    def depart_list_item(self, node):
        self.in_item = False
        self.close_expose_run()
        self.item_depth -= 1

    def visit_definition_list(self, node):
        pass

    def visit_definition_list_item(self, node):
        # possibly mark the item contents as a new expose run
        self.item_depth += 1
        self.mark_expose_run(node)

    def depart_definition_list_item(self, node):
        self.close_expose_run()
        self.item_depth -= 1

    def visit_term(self, node):
        self.break_paragraph()
        self.in_item = False
    def visit_definition(self, node):
        style = {}
        left_margin = self.current_style.get('margin_left') or 0
        tab_stops = self.current_style.get('tab_stops')
        if tab_stops:
            tab_stops = list(tab_stops)
        else:
            tab_stops = []
        tab_stops.append(left_margin + 30)
        style['margin_left'] = left_margin + 30
        style['tab_stops'] = tab_stops
        self.push_style(node, style)
        self.in_item = True
    def depart_definition(self, node):
        self.in_item = False

    def visit_block_quote(self, node):
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
    # Style and layout
    #
    def visit_load_style(self, node):
        self.stylesheet.update(node.get_style())
        self.stack = []
        self.push_style('default', self.stylesheet['default'])
        self.next_style = dict(self.current_style)

    def visit_page_load_style(self, node):
        self.next_stylesheet = self.stylesheet.copy()
        self.visit_load_style(node)

    def visit_style(self, node):
        # XXX detect changes in footer style
        for key, value in node.attlist():
            if '.' in key:
                group, key = key.split('.')
            else:
                group = 'default'
                self.push_style('style-element', {key: value})
            self.stylesheet[group][key] = value

    def visit_page_style(self, node):
        self.next_stylesheet = self.stylesheet.copy()
        self.visit_style(node)

    def visit_layout(self, node):
        # update the current layout using the node contents
        layout.LayoutParser(self.stylesheet['layout']).parse(node.get_layout())

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
        method = getattr(self.decoder, 'visit_%s' % node_name,
             self.decoder.visit_unknown)
        method(node)

    def dispatch_departure(self, node):
        self.decoder.pop_style(node)
        node_name = node.__class__.__name__
        method = getattr(self.decoder, 'depart_%s' % node_name,
             self.decoder.depart_unknown)
        method(node)


def parse(text, stylesheet, bullet_mode):
    # everything is UTF-8, suckers
    text = text.decode('utf8')

    d = DocutilsDecoder(stylesheet, bullet_mode)
    d.decode(text)
    return d.pages

__all__ = ['parse']

