import re
import pyglet
from pyglet.text.formats.structured import ImageElement

import docutils.parsers.rst
import docutils.utils
import docutils.nodes
import docutils.frontend
from docutils.transforms import references
import docutils.writers.html4css1

from bruce import page

newline_replace = re.compile(r'[\n\r]+')

bullets = u'\u25cf\u25cb\u25a1'*3 # (just in case)
def bullet_generator(bullet):
    while 1:
        yield bullet

def number_generator(node):
    # XXX use node.enumtype
    i = 1
    while 1:
        yield '%s%d%s'%(node['prefix'], i, node['suffix'])
        i += 1

class config(docutils.nodes.Special, docutils.nodes.Invisible, docutils.nodes.Element):
    def get_config(self):
        return self.rawsource

def config_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    #required_arguments = 0
    #optional_arguments = 0
    text = '\n'.join(content)
    return [ config(text) ]
config_directive.arguments = (0, 0, 0)
config_directive.content = True
docutils.parsers.rst.directives.register_directive('config', config_directive)


class RstTextPage(page.Page):
    name = 'rst-text'

    def __init__(self, *args, **kw):
        self.styles = kw.pop('styles')
        self.images = kw.pop('images')
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

        self.document = pyglet.text.document.FormattedDocument(self.content)
        for s, e, style in self.styles:
            self.document.set_style(s, e, style)

        for pos, im in self.images:
            im = pyglet.image.load(im)
            self.document.insert_element(pos, ImageElement(im))

        # render the text lines to our batch
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.begin_update()
        self.layout.valign = 'top'
        self.layout.y = vh
        self.layout.end_update()

    def on_leave(self):
        self.document = None
        for decoration in self.decorations:
            decoration.delete()
        self.decorations = []
        self.layout.delete()
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

class Translator(docutils.nodes.GenericNodeVisitor):
    def __init__(self, document):
        docutils.nodes.GenericNodeVisitor.__init__(self, document)
        self.config = dict(
            text=dict(font_name='Bitstream Vera Sans', font_size=20),
            literal=dict(font_name='Courier New'),
            literal_block=dict(font_name='Courier New', margin_left=20),
            bullet_list=dict(margin_left=20),
            enumerated_list=dict(margin_left=20),
            list_item=dict(),
            title=dict(font_size=28, margin_bottom=20, bold=True),
            emphasis=dict(italic=True),
            strong=dict(bold=True),
            paragraph=dict(margin_top=5, margin_bottom=5),
        )

        self.pages = []

    def default_visit(self, node):
        raise NotImplementedError(str(node))
    def default_departure(self, node):
        raise NotImplementedError(str(node))

    def visit_config(self, node):
        for line in node.get_config().splitlines():
            key,value = line.strip().split('=')
            group, key = key.split('.')
            if key == 'font_name': value=str(value)
            self.config[group][key] = value
    def depart_config(self, node):
        pass

    def visit_document(self, node):
        self.source = node.source
    def depart_document(self, node):
        pass

    def visit_section(self, node):
        #print 'SECTION:', node
        self.text_content = ''
        # this is the eventual content position that we keep track of because we're
        # not inserting the image elements into the content as we go.
        self.document_length = 0
        self.document_styles = []
        self.document_images = []
        self.style_stack = []
        self.list_stack = []
        self.section_start_line = node.line
        self.section_end_line = 0
        self.collapse_newlines = True
        self.first_paragraph = True
        self.start_style(**self.config['text'])

    def add_text(self, text):
        self.text_content += text
        self.document_length += len(text)

    def break_para(self):
        '''Break the previous paragraphish.
        '''
        if self.first_paragraph:
            self.first_paragraph = False
            return
        self.add_text('\n')

    def depart_section(self, node):
        self.styled_depart(node)
        self.document_styles.reverse()
        # XXX source stuff here isn't complete (need original text)
        self._page = RstTextPage(self.text_content, self.section_start_line,
            self.section_end_line, '', images=self.document_images,
            styles=self.document_styles, bgcolor='255,255,255,255')
        self.pages.append(self._page)

    def start_style(self, **style):
        # use the length of the actual text for styling because the images haven't
        # been inserted into the document yet
        self.style_stack.append((len(self.text_content), style))

    def pop_style(self):
        start, style = self.style_stack.pop()
        self.document_styles.append((start, len(self.text_content), style))

    def styled_depart(self, node):
        self.pop_style()
        self.section_end_line = node.line

    def nop(self, node):
        self.section_end_line = node.line

    def prune(self, node):
        raise docutils.nodes.SkipNode

    def visit_title(self, node):
        self.break_para()
        self.start_style(**self.config['title'])
    def depart_title(self, node):
        self.styled_depart(node)

    def visit_emphasis(self, node):
        self.start_style(**self.config['emphasis'])
    depart_emphasis = styled_depart

    def visit_strong(self, node):
        self.start_style(**self.config['strong'])
    depart_strong = styled_depart

    def visit_image(self, node):
        # if the parent is structural - document, section, etc then we need
        # to break the previous paragraphish
        if isinstance(node.parent, docutils.nodes.Structural):
            self.break_para()
        self.document_images.append((self.document_length, node['uri']))
        self.document_length += 1
    depart_image = nop

    _paragraph_suppress_newline = False
    def visit_paragraph(self, node):
        if not self._paragraph_suppress_newline:
            self.break_para()
        self._paragraph_suppress_newline = False
        self.start_style(**self.config['paragraph'])
    depart_paragraph = styled_depart

    def visit_bullet_list(self, node):
        self.break_para()
        indent = self.config['bullet_list']['margin_left']
        if self.list_stack:
            depth = self.list_stack[-1][0] + indent
        else:
            depth = indent
        self.start_style(margin_left=depth)
        self.list_stack.append((depth, bullet_generator(bullets[0])))
    def depart_bullet_list(self, node):
        self.styled_depart(node)
        self.list_stack.pop()

    def visit_enumerated_list(self, node):
        self.break_para()
        indent = self.config['enumerated_list']['margin_left']
        if self.list_stack:
            depth = self.list_stack[-1][0] + indent
        else:
            depth = indent
        self.start_style(margin_left=depth)
        self.list_stack.append((depth, number_generator(node)))
    def depart_enumerated_list(self, node):
        self.styled_depart(node)
        self.list_stack.pop()

    def visit_list_item(self, node):
        self.break_para()
        self.start_style(**self.config['list_item'])
        self.add_text(self.list_stack[-1][1].next())
        self._paragraph_suppress_newline = True
    def depart_list_item(self, node):
        pass

    def visit_literal_block(self, node):
        self.collapse_newlines = False
        self.break_para()
        self.start_style(**self.config['literal_block'])
    def depart_literal_block(self, node):
        self.collapse_newlines = True
        self.styled_depart(node)

    def visit_literal(self, node):
        self.start_style(**self.config['literal'])
    def depart_literal(self, node):
        self.styled_depart(node)

    def visit_comment(self, node):
        # XXX comment
        self.prune(node)
    def depart_comment(self, node):
        pass # XXX comment

    def visit_note(self, node):
        # XXX comment
        self.prune(node)
    def depart_note(self, node):
        pass # XXX comment

    visit_system_message = prune
    depart_system_message = nop

    # don't care about the definitions
    visit_substitution_definition = prune
    depart_substitution_definition = nop

    def visit_footer(self, node):
        # XXX save off and attach to the presentation
        #print 'FOOTER:', node
        self.text_content = ''
        self.document_styles = []
        self.style_stack = []
        self.list_stack = []
        self.section_start_line = node.line
        self.section_end_line = 0
        self.start_style(font_size=24, font_name='Arial',
            color=(255, 255, 255, 255))
    def depart_footer(self, node):
        self.styled_depart(node)
        self.document_styles.reverse()
        # XXX do something with the footer

    def visit_Text(self, node):
        text = node.astext()
        if self.collapse_newlines:
            text = newline_replace.sub(' ', text)
        self.add_text(text)
    def depart_Text(self, node):
        pass

def parse(text, html=False):
    assert not html, 'use rst2html for html!'

    # everything is UTF-8, suckers
    text = text.decode('utf8')

    parser = docutils.parsers.rst.Parser()
    settings = docutils.frontend.OptionParser().get_default_values()
    settings.tab_width = 8
    settings.pep_references = False
    settings.rfc_references = False
    document = docutils.utils.new_document('bruce-doc', settings)
    parser.parse(text, document)

    references.Substitutions(document).apply()

    t = Translator(document)
    document.walkabout(t)
    return t.pages

__all__ = ['parse']

