from docutils import nodes
from docutils.parsers.rst import directives

import pyglet

#
# Video directive
#
class blank(nodes.Node):
    children = []

def blank_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ blank() ]
blank_directive.arguments = (0, 0, 0)
blank_directive.options = {}
blank_directive.content = False
directives.register_directive('blank', blank_directive)
