'''
Ideas:

:push:
:pop:           -- manage style state on a separate stack to allow temporary changes

:reset:         -- reset back to the Bruce default style
'''

import ConfigParser

import pyglet

from docutils import nodes
from docutils.transforms import references
from docutils.parsers.rst import directives

from bruce.color import parse_color
from bruce import layout

from cocos.scenes import transitions
from cocos.director import director

def boolean(value, boolean_true=set('yes true on'.split())):
    return value.lower() in boolean_true
def stripped(argument):
    return argument and argument.strip() or ''
def color(argument):
    if not argument:
        return None
    return tuple(parse_color(argument))
def halignment(argument):
    return directives.choice(argument, ('left', 'center', 'right'))
def valignment(argument):
    return directives.choice(argument, ('top', 'center', 'bottom'))
def expose_options(argument):
    return directives.choice(argument, ('show', 'expose'))
def coordinates(argument):
    return [a.strip() for a in argument.split(',')]

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
        return get(self.rawsource)

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
     'transition.name': stripped,
     'transition.duration': float,

     'list.expose': expose_options,

     'layout.valign': valignment,
     'layout.background_color': color,
     'layout.viewport': coordinates,

     'title.position': coordinates,
     'title.hanchor': halignment,
     'title.vanchor': valignment,

     'footer.position': coordinates,
     'footer.hanchor': halignment,
     'footer.vanchor': valignment,

     'table.heading_background_color': color,
     'table.even_background_color': color,
     'table.odd_background_color': color,
     'table.top_padding': int,
     'table.bottom_padding': int,
     'table.left_padding': int,
     'table.right_padding': int,
     'table.cell_align': halignment,
     'table.cell_valign': valignment,
     'table.border': boolean,
     'table.border_color': color,
}
for group in ('', 'default.', 'literal.', 'emphasis.', 'strong.', 'title.',
        'footer.', 'block_quote.',
        'code_keyword.', 'code_text.', 'code_generic.', 'code_name.',
        'code_name_class.', 'code_name_function.', 'code_literal.',
        'code_punctuation.', 'code_operator.', 'code_comment.',
        ):
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
    '''Container for the styles used in rendering Bruce pages.

    Each page will have an instance of this class attached to it. Each
    modification to the stylesheet is done on a .copy() of the previous style.
    '''
    def __init__(self, **kw):
        if 'layout' not in kw:
            kw['layout'] = layout.Layout(
                valign='top',
                background_color=(255, 255, 255, 255),
                # default viewport=('0', '0', 'w', 'h'),
            )
        super(Stylesheet, self).__init__(**kw)
    def value(self, section, name, default=None):
        return self[section].get(name, self['default'].get(name, default))

    def set(self, compound_name, value):
        '''Handle setting a nested dict value using a potentially compound name.

        Split the name on '.' - if there isn't one then the section is 'default'.
        '''
        if '.' in compound_name:
            section, name = compound_name.split('.')
        else:
            section, name = 'default', compound_name
        if section not in self:
            self[section] = {name: value}
        else:
            self[section][name] = value

    def copy(self):
        new = Stylesheet()
        for k in self:
            new[k] = self[k].copy()
        return new

    def get_transition(self):
        klass = _transitions[self['transition']['name']]
        if klass is None: return None

        kwargs = dict(duration=self['transition']['duration'])

        if klass is transitions.FadeTransition:
            kwargs['color'] = self['layout']['background_color'][:3]

        def _transition(new_scene, klass=klass, kwargs=kwargs):
            director.replace(klass(new_scene, **kwargs))

        return _transition

# set up the default style
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
    list = dict(
        expose='show',
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
    layout = layout.Layout(
        valign='top',
        background_color=(255, 255, 255, 255),
        # default viewport=('0', '0', 'w', 'h'),
    ),
    title = dict(
        font_size=28,
        bold=True,
        position=('w//2', 'h'),
        hanchor='center',
        vanchor='top',
    ),
    footer = dict(
        font_size=16,
        italic=True,
        position=('w//2', '0'),
        hanchor='center',
        vanchor='bottom',
    ),
    transition = dict(
        name='fade',
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

white_on_black = default_stylesheet.copy()
big_centered_wob = big_centered.copy()
for d in (white_on_black, big_centered_wob):
    d['default']['color'] = (0xff, 0xff, 0xff, 0xff)
    d['layout']['background_color'] = (0, 0, 0, 255)

    # table styles
    d['table']['heading_background_color'] = (0x32, 0x32, 0x32, 0xff)
    d['table']['even_background_color'] = (0x10, 0x10, 0x10, 0xff)
    d['table']['odd_background_color'] = (0x10, 0x10, 0x10, 0xff)
    d['table']['border_color'] = (0xff, 0xff, 0xff, 0xff)

    # Pygments styles for code highlighting
    d['code_keyword']['color'] = (0x00, 0x80, 0x00, 0xff)
    d['code_name_class']['color'] = (0xBA, 0xBA, 0x21, 0xff)
    d['code_name_function']['color'] = (0xBA, 0xBA, 0x21, 0xff)
    d['code_literal.color'] = (0xBA, 0x21, 0x21, 0xff)
    d['code_operator']['color'] = (0x66, 0x66, 0x66, 0xff)
    d['code_comment']['color'] = (0x40, 0x80, 0x80, 0xff)


stylesheets = {
    'default': default_stylesheet,
    'big-centered': big_centered,
    'white-on-black': white_on_black,
    'big-centered-wob': big_centered_wob,
}

def get(name):
    if name in stylesheets:
        return stylesheets[name].copy()
    return load(name)

def load(filename):
    '''Locate and load the Bruce Style Sheet file indicated.
    '''
    try:
        f = pyglet.resource.file(filename)
    except pyglet.resource.ResourceNotFoundException:
        if filename.endswith('.bss'):
            raise ValueError('stylesheet file %s not found'%filename)
        try:
            f = pyglet.resource.file(filename + '.bss')
        except pyglet.resource.ResourceNotFoundException:
            raise ValueError('stylesheet file %s not found'%filename)

    directives = parse_directives(f)

    # get the base sheet
    if 'inherit-style' in directives:
        sheet = get(directives['inherit-style'])
    else:
        # default for sanity
        sheet = default_stylesheet.copy()

    styles = directives['style']
    for k in styles:
        sheet.set(k, styles[k])

    if directives['layout']:
        layout.LayoutParser(sheet['layout']).parse('\n'.join(directives['layout']))

    return sheet

class ParseError(Exception):
    pass

def parse_directives(f):
    '''Parse a Bruce Style Sheet file's directives.
    '''
    sections = dict(layout=[], style={})
    section = None

    for line in f:
        # Skip over Python-style single line comments #
        # NOTE: line-end comments are NOT supported
        l = line.strip()
        if not l:
            continue
        if l[0] == '#':
            continue

        # handle section heading
        if l[0] == '[' and l[-1] == ']':
            section = l[1:-1]
            continue

        if section is None:
            raise ParseError('content reached with no [section] heading')

        if section == 'layout':
            sections[section].append(l)
            continue

        # [style] section
        key, value = [s.strip() for s in l.split('=')]

        if key == 'inherit-style':
            sections['inherit-style'] = value
            continue

        if not style_directive.options.has_key(key):
            from warnings import warn
            warn('unknown style directive : %s' % key)
            continue

        if '.' not in key:
            key = 'default.' + key
        sections['style'][key] = style_directive.options[key](value)

    return sections


__all__ = ['get', 'stylesheets']

