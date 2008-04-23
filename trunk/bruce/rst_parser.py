import pyglet

from bruce import page

import docutils.parsers.rst
import docutils.utils
import docutils.nodes
import docutils.frontend
import docutils.writers.html4css1

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

class RstTextPage(page.Page):
    name = 'rst-text'

    def __init__(self, *args, **kw):
        self.styles = kw.pop('styles')
        super(RstTextPage, self).__init__(*args, **kw)

    def on_enter(self, vw, vh):
        super(RstTextPage, self).on_enter(vw, vh)

        self.document = pyglet.text.document.FormattedDocument(self.content)
        for s, e, style in self.styles:
            self.document.set_style(s, e, style)

        # render the text lines to our batch
        self.batch = pyglet.graphics.Batch()
        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document,
            vw, vh, multiline=True, batch=self.batch)
        self.layout.valign = 'top'
        self.layout.y = vh

    def on_leave(self):
        self.document = None
        self.layout = None
        self.batch = None

    def draw(self):
        self.batch.draw()

class Translator(docutils.nodes.GenericNodeVisitor):
    def __init__(self, document):
        docutils.nodes.GenericNodeVisitor.__init__(self, document)
        self.pages = []

    def default_visit(self, node):
        raise NotImplementedError(str(node))
    def default_departure(self, node):
        raise NotImplementedError(str(node))

    def visit_document(self, node):
        self.source = node.source
    def depart_document(self, node):
        pass

    def visit_section(self, node):
        #print 'SECTION:', node
        self._content = ''
        self._styles = []
        self._styles_stack = []
        self._list_stack = []
        self._start = node.line
        self._cur = 0
        self._start_style(font_size=24, font_name='Arial',
            color=(255, 255, 255, 255))

    def depart_section(self, node):
        self.styled_depart(node)

        # source tracking
        self._styles.reverse()
        page = RstTextPage(self._content, 0, 0, '', styles=self._styles)
        self.pages.append(page)

    def _start_style(self, **style):
        self._styles_stack.append((len(self._content), style))

    def styled_depart(self, node):
        start, style = self._styles_stack.pop()
        #print (start, len(self._content), style)
        self._styles.append((start, len(self._content), style))
        self._cur = node.line

    def nop_depart(self, node):
        self._cur = node.line

    def visit_title(self, node):
        self._start_style(font_size=36, bold=True)
    depart_title = styled_depart

    def visit_emphasis(self, node):
        self._start_style(italic=True)
    depart_emphasis = styled_depart

    def visit_strong(self, node):
        self._start_style(bold=True)
    depart_strong = styled_depart

    _paragraph_suppress_newline = False
    def visit_paragraph(self, node):
        if not self._paragraph_suppress_newline:
            self._content += '\n'
        self._paragraph_suppress_newline = False
    depart_paragraph = nop_depart

    def visit_bullet_list(self, node):
        self._content += '\n'
        self._list_stack.append(bullet_generator(bullets[0]))
    def depart_bullet_list(self, node):
        self._list_stack.pop()

    def visit_enumerated_list(self, node):
        self._content += '\n'
        self._list_stack.append(number_generator(node))
    def depart_enumerated_list(self, node):
        self._list_stack.pop()

    def visit_list_item(self, node):
        self._content += '\n' + self._list_stack[-1].next()
        self._paragraph_suppress_newline = True
    depart_list_item = nop_depart

    def visit_literal_block(self, node):
        self._content += '\n'
        self._start_style(font_name='Courier New')
    depart_literal_block = styled_depart

    def visit_decoration(self, node):
        pass
    depart_decoration = nop_depart

    def visit_footer(self, node):
        # XXX save off and attach to the presentation
        #print 'FOOTER:', node
        self._content = ''
        self._styles = []
        self._styles_stack = []
        self._list_stack = []
        self._start = node.line
        self._cur = 0
        self._start_style(font_size=24, font_name='Arial',
            color=(255, 255, 255, 255))
    def depart_footer(self, node):
        self.styled_depart(node)
        self._styles.reverse()
        # XXX do something with the footer

    def visit_Text(self, node):
        self._content += node.astext()
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

    t = Translator(document)
    document.walkabout(t)
    return t.pages

__all__ = ['parse']

