from docutils import nodes
from docutils.parsers.rst import directives

import pyglet

#
# Code directive
#
class code(nodes.Element):
    def astext(self):
        return self.rawsource

def code_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    if arguments:
        lexer_name=arguments[0]
    else:
        lexer_name=None
    return [ code('\n'.join(content), lexer_name=lexer_name) ]
# arguments: 
code_directive.arguments = (0, 1, 0)
code_directive.content = True
directives.register_directive('code', code_directive)

