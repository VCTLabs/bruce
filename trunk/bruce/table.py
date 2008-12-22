import sys
import code

from docutils import nodes

from cocos.director import director

import pyglet
from pyglet.gl import *

from bruce import rst_parser


class TableElement(pyglet.text.document.InlineElement):
    prompt = ">>> "
    prompt_more = "... "

    def __init__(self, document, stylesheet, doctree_node):
        self.doctree_node = doctree_node
        self.stylesheet = stylesheet

        # rough numbers to start with
        self.width = director.get_window_size()[0]

        self.table = TableGenerator(self)
        doctree_node.walkabout(TableVisitor(doctree_node, self.table))
        self.dpi = 96
        self.table.layout(self.width)

        super(TableElement, self).__init__(self.table.height, 0, self.width)

    def set_scale(self, scale):
        # XXX relayout table
        self.dpi = int(scale * 96)

    def on_enter(self, w, h):
        pass

    def place(self, layout, x, y):
        self.table.place(layout, x, y)

    def remove(self, layout):
        self.table.delete_layout(layout)

    def on_exit(self):
        pass


class DummyReporter(object):
    def debug(*args): pass

class DummyDocument(object):
    reporter = DummyReporter()

class TableVisitor(rst_parser.DocutilsVisitor):
    def __init__(self, node, decoder):
        document = DummyDocument()
        nodes.NodeVisitor.__init__(self, document)
        self.decoder = decoder

class TableGenerator(object):
    def __init__(self, element):
        self.element = element
        self.rows = self.columns = 0
        self.cells = {}
        self.cell_layouts = {}
        self.column_specs = []
        self.cell_decoration = {}

        # layout spec
        # XXX maybe allow multiple layouts?
        self.parent_layout = self.x = self.y = None

    def layout(self, width):
        # figure column widths
        specwidth = float(sum(self.column_specs))
        self.colwidths = [int(w/specwidth*width)
            for w in self.column_specs]

        # figure row heights
        self.row_heights = []
        for row in range(self.rows):
            rowheight = 0
            for col in range(self.columns):
                colwidth = self.colwidths[col]
                document = self.cells[row, col]
                l = pyglet.text.layout.IncrementalTextLayout(
                    document, colwidth, 50, dpi=self.element.dpi,
                    multiline=True)
                rowheight = max(rowheight, l.content_height)
                l.delete()
                # XXX figure columnd widths too
            self.row_heights.append(rowheight)
        self.height = sum(self.row_heights)

    def full_layout(self, layout):
        # organise the layers
        foreground = pyglet.graphics.OrderedGroup(1, layout.top_group)
        background = pyglet.graphics.OrderedGroup(0, layout.top_group)

        # place in the real layout
        for row in range(self.rows):
            height = self.row_heights[row]
            for col in range(self.columns):
                colwidth = self.colwidths[col]
                document = self.cells[row, col]
                l = pyglet.text.layout.IncrementalTextLayout(
                    document, colwidth, height, dpi=self.element.dpi,
                    multiline=True, batch=layout.batch, group=foreground)
                self.cell_layouts[row, col] = l

        style = self.element.stylesheet['table']
        for row in range(self.rows):
            height = self.row_heights[row]
            x = 0
            for col in range(self.columns):
                colwidth = self.colwidths[col]
                x2 = x + colwidth
                if row%2:
                    color = style['odd_background_color']
                else:
                    color = style['even_background_color']
                r = layout.batch.add(4, pyglet.gl.GL_QUADS, background,
                    ('v2i', (x, 0, x2, 0, x2, height, x, height)),
                    ('c4B', color * 4),
                )
                x = x2
                self.cell_decoration[row, col] = r

        self.parent_layout = layout
        self.x = self.y = None

    _r = None
    def place(self, layout, x, y):
        '''Place myself in the layout where (x, y) define the lower-left corner
        of my bounding box.
        '''
        if self.parent_layout is not layout:
            self.full_layout(layout)

        if self.x == x and self.y == y:
            return

        # move layout
        self.move_layout(x, y)

    def move_layout(self, x, y):
        # we lay out from the top so start at the top
        ry = y + sum(self.row_heights)
        for row in range(self.rows):
            cx = x
            height = self.row_heights[row]
            for column in range(self.columns):
                # update layout
                l = self.cell_layouts[row, column]
                l.begin_update()
                l.anchor_y = 'top'
                l.y = ry
                l.x = cx
                l.end_update()

                # update decoration
                colwidth = self.colwidths[column]
                x2 = cx + colwidth
                r = self.cell_decoration[row, column]
                r.vertices[:] = [cx, ry-height, x2, ry-height, x2, ry, cx, ry]

                cx += self.colwidths[column]

            ry -= height

        self.x, self.y = x, y

    def delete_layout(self, layout):
        for v in self.cell_layouts.values():
            v.delete()
        self.cell_layouts = {}
        for v in self.cell_decoration.values():
            v.delete()
        self.cell_decoration = {}
        self.layout = self.x = self.y = None

    def pop_style(self, *args):
        # NOP - we don't track styles
        pass

    def visit_table(self, node): pass
    def visit_tgroup(self, node): pass
    def visit_tbody(self, node): pass

    def visit_colspec(self, node):
        self.column_specs.append(int(node['colwidth']))

    def visit_row(self, node):
        self.columns = 0

    def depart_row(self, node):
        self.rows += 1

    def visit_unknown(self, node):
        raise ValueError('UNKNOWN %s'%node.__class__.__name__)
    def depart_unknown(self, node):
        pass

    def visit_entry(self, node):
        # XXX assert no col/row spanning etc
        g = rst_parser.DocumentGenerator(self.element.stylesheet, None)
        self.cells[self.rows, self.columns] = g.decode(node)
        self.columns += 1
        raise nodes.SkipNode

