'''
Ideas:

:push:
:pop:           -- manage style state on a separate stack to allow temporary changes

:reset:         -- reset back to the Bruce default style
'''

from docutils import nodes
from docutils.transforms import references
from docutils.parsers.rst import directives

from bruce.color import parse_color

#from bruce.decoration import Decoration

# XXX validate the values here
def is_boolean(value, boolean_true = set('yes true on'.split())):
    return value in boolean_true
def stripped(argument):
    return argument and argument.strip() or ''
def color(argument):
    return parse_color(argument)
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
     'layout.valign': valignment,
     'block_quote.italic': is_boolean,
     'block_quote.bold': is_boolean,
}
for group in ('', 'default.', 'literal.', 'emphasis.', 'strong.', 'title.', 'footer.'):
    style_directive.options[group + 'color'] = color
    style_directive.options[group + 'font_size'] = directives.positive_int
    style_directive.options[group + 'font_name'] = stripped
    style_directive.options[group + 'bold'] = is_boolean
    style_directive.options[group + 'italic'] = is_boolean

for group in ('', 'default.', 'title.', 'footer.'):
    style_directive.options[group + 'align'] = halignment

for group in 'default literal_block line_block'.split():
    for margin in 'left right top bottom'.split():
        style_directive.options[group + '.margin_' + margin] = directives.positive_int

style_directive.content = False
directives.register_directive('style', style_directive)

class Stylesheet(dict):
    def value(self, section, name, default=None):
        return self[section].get(name, self['default'].get(name, default))

    def copy(self):
        new = Stylesheet()
        for k in self:
            new[k] = self[k].copy()
        return new

default_stylesheet = Stylesheet(
    default = dict(
        font_name='Arial',
        font_size=20,
        margin_bottom=12,
        align='left',
        color=(0,0,0,255),
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
    line_block = dict(
        margin_left=40,
    ),
    block_quote = dict(
        italic=True,
        bold=False,
    ),
    title = dict(
        font_size=28,
        align='center',
        bold=True,
    ),
    footer = dict(
        font_size=16,
        align='center',
        italic=True,
    ),
    layout = dict(
        valign='top',
    ),
    #decoration = Decoration(''),
)

__all__ = ['default_stylesheet']

