from docutils import nodes
from docutils.transforms import references
from docutils.parsers.rst import directives

from bruce.decoration import Decoration

def is_boolean(value, boolean_true = set('yes true on'.split())):
    return value in boolean_true
def stripped(argument):
    return argument and argument.strip() or ''
def halignment(argument):
    return directives.choice(argument, ('left', 'center', 'right'))
def valignment(argument):
    return directives.choice(argument, ('top', 'center', 'bottom'))

#
# Style directive
#
class style(nodes.Special, nodes.Invisible, nodes.Element):
    def get_style(self):
        return self.rawsource

def style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ style('', **options) ]
style_directive.arguments = (0, 0, 0)
style_directive.options = {
     'align': halignment, # synonym for...
     'default.align': halignment,
     'layout.valign': valignment,
}
for group in ('', 'default.','literal.','emphasis.','strong.'):
    style_directive.options[group + 'font_size'] = directives.positive_int
    style_directive.options[group + 'font_name'] = stripped
    style_directive.options[group + 'bold'] = is_boolean
    style_directive.options[group + 'italic'] = is_boolean

for group in 'default literal_block'.split():
    for margin in 'left right top bottom'.split():
        style_directive.options[group + '.margin_' + margin] = directives.positive_int

style_directive.content = False
directives.register_directive('style', style_directive)

default_stylesheet = dict(
    default = dict(
        font_name='Arial',
        font_size=20,
        margin_bottom=12,
        align='left',
    ),
    emphasis = dict(
        italic=True,
    ),
    strong = dict(
        bold=True,
    ),
    literal = dict(
        font_name='Courier New',
        font_size=20,
    ),
    literal_block = dict(
        margin_left=20,
    ),
    layout = dict(
        valign='top',
    ),
    decoration = Decoration(''),
)

def copy_stylesheet(d):
    new = {}
    for k in d:
        new[k] = d[k].copy()
    return new

__all__ = 'default_stylesheet copy_stylesheet'.split()

