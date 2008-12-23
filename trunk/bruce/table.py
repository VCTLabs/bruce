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

        self.table = TableGenerator(self)
        doctree_node.walkabout(TableVisitor(doctree_node, self.table))
        self.scale = 1.0
        self.dpi = 96
        self.table.layout()

        super(TableElement, self).__init__(self.table.height, 0, self.table.width)

    def set_scale(self, scale):
        if scale != self.scale:
            return

        self.dpi = int(scale * 96)
        # XXX relayout table

    def place(self, layout, x, y):
        self.table.place(layout, x, y)

    def remove(self, layout):
        self.table.delete_layout(layout)


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
        self.num_rows = self.num_columns = 0
        self.cells = {}
        self.cell_layouts = {}
        self.column_specs = []
        self.cell_decoration = {}
        self.body_rows = set()
        self.heading_rows = set()

        # layout spec
        # XXX maybe allow multiple layouts?
        self.parent_layout = self.x = self.y = None

    def layout(self):
        width = director.get_window_size()[0]

        # figure column widths
        specwidth = float(sum(self.column_specs))
        spec_widths = [int(w/specwidth*width)
            for w in self.column_specs]

        # padding
        style = self.element.stylesheet['table']
        vpad = style['top_padding'] + style['bottom_padding']
        hpad = style['left_padding'] + style['right_padding']

        # figure row heights
        self.row_heights = []
        self.column_widths = [0]*self.num_columns
        for row in range(self.num_rows):
            rowheight = 0
            for col in range(self.num_columns):
                width = spec_widths[col]
                document = self.cells[row, col]
                l = pyglet.text.layout.IncrementalTextLayout(
                    document, width, 50, dpi=self.element.dpi,
                    multiline=True)
                rowheight = max(rowheight, l.content_height)
                width = l.content_width + hpad
                width += 1      # seems to be a rounding error
                self.column_widths[col] = max(width, self.column_widths[col])
                l.delete()
            if style['border']:
                if row in self.heading_rows:
                    # heading row
                    rowheight += 3
                elif row != self.num_rows - 1:
                    # regular row
                    rowheight += 1
            self.row_heights.append(rowheight+vpad)
        self.height = sum(self.row_heights)
        self.width = sum(self.column_widths)

    def full_layout(self, layout):
        self.parent_layout = layout
        self.x = self.y = None

        # organise the layers
        foreground = pyglet.graphics.OrderedGroup(1, layout.top_group)
        background = pyglet.graphics.OrderedGroup(0, layout.top_group)

        # style info
        style = self.element.stylesheet['table']
        vpad = style['top_padding'] + style['bottom_padding']
        hpad = style['left_padding'] + style['right_padding']

        # place in the real layout
        for row in range(self.num_rows):
            height = self.row_heights[row]-vpad
            if style['border']:
                if row in self.heading_rows:
                    # heading row
                    height -= 3
                elif row != self.num_rows - 1:
                    # regular row
                    height -= 1
            for col in range(self.num_columns):
                document = self.cells[row, col]
                l = pyglet.text.layout.IncrementalTextLayout(
                    document, self.column_widths[col]-hpad, height,
                    dpi=self.element.dpi, multiline=True,
                    batch=layout.batch, group=foreground)
                self.cell_layouts[row, col] = l

        # cell backgrounds
        for row in range(self.num_rows):
            height = self.row_heights[row]
            x = 0
            for col in range(self.num_columns):
                colwidth = self.column_widths[col]
                x2 = x + colwidth
                if row in self.heading_rows:
                    color = style['heading_background_color']
                elif row%2:
                    color = style['odd_background_color']
                else:
                    color = style['even_background_color']
                r = layout.batch.add(4, pyglet.gl.GL_QUADS, background,
                    ('v2i', (x, 0, x2, 0, x2, height, x, height)),
                    ('c4B', color * 4),
                )
                x = x2
                self.cell_decoration[row, col] = r

        # border lines
        if style['border']:
            color = style['border_color']
            l = [0] * 4 * (self.num_rows-1 + self.num_columns-1)
            n = len(l)//2
            self.border_decoration = layout.batch.add(n,
                pyglet.gl.GL_LINES, foreground,
                ('v2i', l), ('c4B', color * n),
            )

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
        # style info
        style = self.element.stylesheet['table']

        # we lay out from the top so start at the top
        ry = y + sum(self.row_heights)
        for row in range(self.num_rows):
            cx = x
            height = self.row_heights[row]
            for column in range(self.num_columns):
                # update layout
                l = self.cell_layouts[row, column]
                l.begin_update()
                l.anchor_y = 'top'
                l.y = ry - style['top_padding']
                l.x = cx + style['left_padding']
                l.end_update()

                # update decoration
                colwidth = self.column_widths[column]
                x2 = cx + colwidth
                r = self.cell_decoration[row, column]
                r.vertices[:] = [cx, ry-height, x2, ry-height, x2, ry, cx, ry]

                cx += self.column_widths[column]

            ry -= height

        if style['border']:
            w = sum(self.column_widths)
            h = sum(self.row_heights)
            l = []
            ry = y + sum(self.row_heights)
            for row in range(self.num_rows-1):
                ry -= self.row_heights[row]
                l.extend([x, ry, x+w, ry])
            cx = x
            for col in range(self.num_columns-1):
                cx += self.column_widths[col]
                l.extend([cx, y, cx, y+h])
            self.border_decoration.vertices[:] = l

        self.x, self.y = x, y

    def delete_layout(self, layout):
        for v in self.cell_layouts.values():
            v.delete()
        self.cell_layouts = {}
        for v in self.cell_decoration.values():
            v.delete()
        self.cell_decoration = {}
        self.border_decoration.delete()
        self.border_decoration = None
        self.layout = self.x = self.y = None

    def pop_style(self, *args):
        # NOP - we don't track styles
        pass

    def visit_table(self, node): pass
    def visit_tgroup(self, node): pass
    def visit_tbody(self, node):
        self._content_section = self.body_rows
    def visit_thead(self, node):
        self._content_section = self.heading_rows

    def visit_colspec(self, node):
        self.column_specs.append(int(node['colwidth']))

    def visit_row(self, node):
        self.num_columns = 0
        self._content_section.add(self.num_rows)

    def depart_row(self, node):
        self.num_rows += 1

    def visit_unknown(self, node):
        raise ValueError('UNKNOWN %s'%node.__class__.__name__)
    def depart_unknown(self, node):
        pass

    def visit_entry(self, node):
        # XXX assert no col/row spanning etc
        g = rst_parser.DocumentGenerator(self.element.stylesheet, None)
        self.cells[self.num_rows, self.num_columns] = g.decode(node)
        self.num_columns += 1
        raise nodes.SkipNode

