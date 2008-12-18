import sys
import code

from docutils import nodes

import pyglet
from pyglet.gl import *

from bruce import rst_parser

class TableGenerator(object):
    def __init__(self, element):
        self.element = element

    def visit_table(self, node):
        pass

    def visit_tgroup(self, node):
        pass

    def visit_colspec(self, node):
        pass
        
    def visit_tbody(self, node):
        pass

    def visit_row(self, node):
        print 'NEW ROW'

    def visit_unknown(self, node):
        print 'UNKNOWN', node

    def visit_entry(self, node):
        # XXX assert no col/row spanning etc
        print 'RUN DOCUMENT GENERATOR ON', 

class DummyReporter(object):
    def debug(*args): pass

class DummyDocument(object):
    reporter = DummyReporter()

class TableVisitor(rst_parser.DocutilsVisitor):
    def __init__(self, node, decoder):
        document = DummyDocument()
        nodes.NodeVisitor.__init__(self, document)
        self.decoder = decoder

class TableElement(pyglet.text.document.InlineElement):
    prompt = ">>> "
    prompt_more = "... "

    def __init__(self, document, stylesheet, doctree_node):
        self.doctree_node = doctree_node
        self.stylesheet = stylesheet

        self.table = TableGenerator(self)
        doctree_node.walkabout(TableVisitor(doctree_node, self.table))

        self.width = self.width_spec = 100
        self.height = self.height_spec = 100

        self.layout = None

        super(TableElement, self).__init__(self.height, 0, self.width)

    def set_scale(self, scale):
        self.width = int(self.width_spec * scale)
        self.height = int(self.height_spec * scale)
        self.dpi = int(scale * 96)

        # update InlineElement attributes
        self.ascent = self.height
        self.descent = 0
        self.advance = self.width

        # force re-layout if we're laid out
        if self.layout is not None:
            self.layout.delete()
            self.layout = None
            self.quad.delete()

    def on_enter(self, w, h):
        pass

    def place(self, layout, x, y):
        pass

    def remove(self, layout):
        pass

    def on_exit(self):
        pass

