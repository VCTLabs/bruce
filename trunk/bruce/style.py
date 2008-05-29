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

def is_boolean(value, boolean_true = set('yes true on'.split())):
    return value in boolean_true
def stripped(argument):
    return argument and argument.strip() or ''
def color(argument):
    if not argument:
        return None
    return parse_color(argument)
def halignment(argument):
    return directives.choice(argument, ('left', 'center', 'right'))
def valignment(argument):
    return directives.choice(argument, ('top', 'center', 'bottom'))

#
# Style directive
#
class load_style(nodes.Special, nodes.Invisible, nodes.Element):
    def get_style(self):
        if self.rawsource in stylesheets:
            return stylesheets[self.rawsource]
        else:
            raise NotImplementedError('loading of stylesheets not implemented')
def load_style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ load_style(arguments[0]) ]
load_style_directive.arguments = (1, 0, 1)
load_style_directive.content = False
directives.register_directive('load-style', load_style_directive)

class style(nodes.Special, nodes.Invisible, nodes.Element):
    def get_style(self):
        return self.rawsource

def style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ style('', **options) ]
style_directive.arguments = (0, 0, 0)
style_directive.options = {
     'layout.valign': valignment,
}
for group in ('', 'default.', 'literal.', 'emphasis.', 'strong.', 'title.',
        'footer.', 'block_quote.'):
    style_directive.options[group + 'color'] = color
    style_directive.options[group + 'background_color'] = color
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
        background_color=(220, 220, 220, 255),
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
)

big_centered = default_stylesheet.copy()
big_centered['default']['font_size'] = 64
big_centered['default']['align'] = 'center'
big_centered['default']['margin_bottom'] = 32
big_centered['literal']['font_size'] = 64
big_centered['title']['font_size'] = 84
big_centered['layout']['valign'] = 'center'

stylesheets = {
    'default': default_stylesheet,
    'big-centered': big_centered,
}

__all__ = ['default_stylesheet']

