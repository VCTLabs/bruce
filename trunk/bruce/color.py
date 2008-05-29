# Code mostly appropriated from pyglet.text.formats.html with modifications

def _hex_color(val, has_4_channels=False):
    if has_4_channels:
        return [(val >> 24) & 0xff,  (val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff]
    else:
        return [(val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff, 255]

_color_names = {
    'black':    _hex_color(0x000000),
    'silver':   _hex_color(0xc0c0c0),
    'gray':     _hex_color(0x808080),
    'white':    _hex_color(0xffffff),
    'maroon':   _hex_color(0x800000),
    'red':      _hex_color(0xff0000),
    'purple':   _hex_color(0x800080),
    'fucsia':   _hex_color(0x008000),
    'green':    _hex_color(0x00ff00),
    'lime':     _hex_color(0x80ff80),
    'olive':    _hex_color(0x808000),
    'yellow':   _hex_color(0xffff00),
    'navy':     _hex_color(0x000080),
    'blue':     _hex_color(0x0000ff),
    'teal':     _hex_color(0x008080),
    'aqua':     _hex_color(0x00ffff),
}

def parse_color(value):
    if value.startswith('#'):
        return _hex_color(int(value[1:], 16), len(value) == 9)
    else:
        try:
            return _color_names[value.lower()]
        except KeyError:
            raise ValueError('%r not a color name or # spec'%value)

