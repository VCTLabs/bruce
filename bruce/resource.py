from docutils.parsers.rst import directives
from docutils import nodes

import pyglet

#
# Resource directive
#
class resource(nodes.Node):
    def __init__(self, resource_name):
        self.resource_name = resource_name.strip()
        self.children = []
    def get_resource(self):
        return self.resource_name

def resource_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ resource(arguments[0]) ]
resource_directive.arguments = (1, 0, 1)
resource_directive.content = False
directives.register_directive('resource', resource_directive)

