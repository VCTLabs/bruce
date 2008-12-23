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

from cocos.scenes import transitions
from cocos.director import director

def boolean(value, boolean_true=set('yes true on'.split())):
    return value.lower() in boolean_true
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

_transitions = dict(
    # do not require VBO support
    none=None,
    fade=transitions.FadeTransition,
    move_in_left=transitions.MoveInLTransition,
    move_in_right=transitions.MoveInRTransition,
    move_in_bottom=transitions.MoveInBTransition,
    move_in_top=transitions.MoveInTTransition,
    slide_in_left=transitions.SlideInLTransition,
    slide_in_right=transitions.SlideInRTransition,
    slide_in_bottom=transitions.SlideInBTransition,
    slide_in_top=transitions.SlideInTTransition,
    roto_zoom=transitions.RotoZoomTransition,
    jump_zoom=transitions.JumpZoomTransition,
    shrink_grow=transitions.ShrinkGrowTransition,

    # require VBO support
    flip_x=transitions.FlipX3DTransition,
    flip_y=transitions.FlipY3DTransition,
    flip_angle=transitions.FlipAngular3DTransition,
    shuffle=transitions.ShuffleTransition,
    turn_off_tiles=transitions.TurnOffTilesTransition,
    fade_top_right=transitions.FadeTRTransition,
    fade_bottom_left=transitions.FadeBLTransition,
    fade_up=transitions.FadeUpTransition,
    fade_down=transitions.FadeDownTransition,
    corner_move=transitions.CornerMoveTransition,
    envelope=transitions.EnvelopeTransition,
    split_rows=transitions.SplitRowsTransition,
    split_cols=transitions.SplitColsTransition,
)

#
# Style directive
#
class load_style(nodes.Special, nodes.Invisible, nodes.Element):
    '''Document tree node representing a style loading directive.
    '''
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
    '''Document tree node representing a style directive.
    '''
    def get_style(self):
        return self.rawsource

def style_directive(name, arguments, options, content, lineno,
                          content_offset, block_text, state, state_machine):
    return [ style('', **options) ]
style_directive.arguments = (0, 0, 0)
style_directive.options = {
     'layout.valign': valignment,
     'layout.background_color': color,
     'transition.name': stripped,
     'transition.duration': float,
     'table.heading_background_color': color,
     'table.even_background_color': color,
     'table.odd_background_color': color,
     'table.top_padding': int,
     'table.bottom_padding': int,
     'table.left_padding': int,
     'table.right_padding': int,
     'table.border': boolean,
     'table.border_color': color,
}
for group in ('', 'default.', 'literal.', 'emphasis.', 'strong.', 'title.',
        'footer.', 'block_quote.'):
    style_directive.options[group + 'color'] = color
    style_directive.options[group + 'background_color'] = color
    style_directive.options[group + 'font_size'] = directives.positive_int
    style_directive.options[group + 'font_name'] = stripped
    style_directive.options[group + 'bold'] = boolean
    style_directive.options[group + 'italic'] = boolean

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

    def get_transition(self):
        klass = _transitions[self['transition']['name']]
        if klass is None: return None
        def _transition(new_scene, klass=klass, duration=self['transition']['duration']):
            director.replace(klass(new_scene, duration=duration))
        return _transition

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
        # XXX reinstate if we can bg the whole block
        #background_color=(220, 220, 220, 255),
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
        bold=True,
    ),
    footer = dict(
        font_size=16,
        italic=True,
    ),
    layout = dict(
        valign='top',
        background_color=(255, 255, 255, 255),
    ),
    transition = dict(
        name='none',
        duration=0.5,
    ),

    # Pygments styles for code highlighting
    code_keyword = dict(
        color = (0, 0x80, 0, 255),
    ),
    code_text = dict(
    ),
    code_generic = dict(
    ),
    code_name = dict(
        bold=True,
    ),
    code_name_class = dict(
        bold=True,
        color=(0xBA, 0xBA, 0x21, 255),
    ),
    code_name_function = dict(
        bold=True,
        color=(0xBA, 0xBA, 0x21, 255),
    ),
    code_literal = dict(
        color=(0xBA, 0x21, 0x21, 255),
    ),
    code_punctuation = dict(
    ),
    code_operator = dict(
        color=(0x66, 0x66, 0x66, 255),
    ),
    code_comment = dict(
        italic=True,
        color=(0x40, 0x80, 0x80, 255),
    ),

    table = dict(
        heading_background_color=(210, 210, 210, 255),
        even_background_color=(240, 240, 240, 255),
        odd_background_color=(240, 240, 240, 255),
        cell_align='left',
        cell_valign='top',
        top_padding=2,
        bottom_padding=2,
        left_padding=4,
        right_padding=4,
        border=True,
        border_color=(0, 0, 0, 255),
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

__all__ = ['default_stylesheet', 'stylesheets']

