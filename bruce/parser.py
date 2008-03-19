import pyglet

class ParseError(Exception):
    def __init__(self, number, error):
        super(ParseError, self).__init__('line %d: %s'%(number, error))

def parse(text, html=False):
    from bruce.presentation import Presentation

    # everything is UTF-8, suckers
    text = text.decode('utf8')

    klass = None
    pages = []
    notes = []
    all = []
    flags_section = False
    pos = 0

    for n, line in enumerate(text.splitlines()):

        pos += len(line) + 1
        if klass is None and not line.startswith('--- '):
            continue

        all.append(line)

        if line.startswith('#'):
            notes.append(line[1:].strip())
        elif line.startswith('--- '):
            first = all[-1]
            all[:] = all[:-1]
            if klass is not None:
                flags['end_pos'] = pos - len(line) - 1
                try:
                    content = '\n'.join(content).strip()
                    if html:
                        obj = (klass.as_html(content, **flags), notes)
                    else:
                        obj = klass.as_page(content, **flags)
                except ValueError, error:
                    raise
                    raise ParseError(N, repr(error))
                klass = None
                if obj:
                    pages.append(obj)
            N = n
            all = [first]
            flags = dict(source=all, start_pos=pos - len(line) - 1)
            content = []
            notes = []
            flags_section = True

            name = line[4:].strip()
            if ' ' in name:
                name, content = name.split(' ', 1)
                content = [content.strip()]
            if name in _classes:
                klass = _classes[name]
                continue

            if not name.startswith('plugin:'):
                raise ParseError(n, '%s not a registered page type'%name)

            name = name[7:] + '.py'
            try:
                f = loader.file(name)
            except pyglet.resource.ResourceNotFoundException:
                raise ParseError(n, '%s not a plugin page type'%name)

            try:
                source = f.read()
            finally:
                f.close()
            d = {}

            # XXX handle errors
            exec source in d

            if 'Page' not in d:
                raise ParseError(n, '%s not a plugin page type'%name)

            klass = d['Page']

        elif flags_section and (line.startswith('  ') or line.startswith('\t')):
            if '=' in line:
                name, value = line.split('=', 1)
                flags[str(name.strip())] = value.strip()
            else:
                flags[str(line.strip())] = True
        else:
            flags_section = False
            content.append(line)

    if klass is not None:
        flags['end_pos'] = pos
        try:
            content = '\n'.join(content)
            if html:
                obj = (klass.as_html(content, **flags), notes)
            else:
                obj = klass.as_page(content, **flags)
        except ValueError, error:
            raise ParseError(N, error)
        if obj:
            pages.append(obj)

    return pages

from bruce import config
from bruce.text import TextPage
from bruce.code import CodePage
from bruce.resource import Resource, loader
from bruce.image import ImagePage
from bruce.video import VideoPage
from bruce.html import HTMLTextPage
from bruce.blank import BlankPage
from bruce.python_interpreter import PythonInterpreterPage
from bruce.python_code import PythonCodePage
_classes = dict(config=config.config, text=TextPage, html=HTMLTextPage,
    image=ImagePage, resource=Resource, video=VideoPage, blank=BlankPage,
    code=CodePage, py=PythonInterpreterPage, pycode=PythonCodePage)
def register(name, klass):
    if name in _classes:
        raise KeyError('%s already registered!'%name)
    _classes[name] = klass

__all__ = 'parse ParseError register'.split()

