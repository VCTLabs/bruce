import sys
import re
import collections

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.core import publish_cmdline, default_description


#
# pygments "code" directive
#
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

# Controls for the pygments code formatter
DEFAULT = HtmlFormatter(noclasses=True)
# Add name -> formatter pairs for every variant you want to use
VARIANTS = {
    # 'linenos': HtmlFormatter(noclasses=INLINESTYLES, linenos=True),
}
def code_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    if arguments:
        lexer = get_lexer_by_name(arguments[0])
    else:
        lexer = get_lexer_by_name('python')
    # take an arbitrary option if more than one is given
    formatter = options and VARIANTS[options.keys()[0]] or DEFAULT
    parsed = highlight(u'\n'.join(content), lexer, formatter)
    return [nodes.raw('', parsed, format='html')]
from bruce import code_block
code_directive.arguments = code_block.code_directive.arguments
code_directive.content = code_block.code_directive.content


#
# style directives
# 
from bruce import style
load_style_directive = lambda *args: []
load_style_directive.arguments = style.load_style_directive.arguments
load_style_directive.content = style.load_style_directive.content
style_directive = lambda *args: []
style_directive.arguments = style.style_directive.arguments
style_directive.options = style.style_directive.options
style_directive.content = style.style_directive.content

#
# Interpreter directive: no output unless default text
# TODO: actually use the default text
from bruce import interpreter
interpreter_directive = lambda *args: []
interpreter_directive.arguments = interpreter.interpreter_directive.arguments
interpreter_directive.options = interpreter.interpreter_directive.options
interpreter_directive.content = interpreter.interpreter_directive.content

#
# miscellaneous directives that have no HTML output
#
from bruce import layout
layout_directive = lambda *args: []
layout_directive.arguments = layout.layout_directive.arguments
layout_directive.content = layout.layout_directive.content

from bruce import blank
blank_directive = lambda *args: []
blank_directive.arguments = blank.blank_directive.arguments
blank_directive.content = blank.blank_directive.content

# TODO: actually use this to fix image etc. paths
from bruce import resource
resource_directive = lambda *args: []
resource_directive.arguments = resource.resource_directive.arguments
resource_directive.content = resource.resource_directive.content

# TODO: use a frame cap
from bruce import video
video_directive = lambda *args: []
video_directive.arguments = video.video_directive.arguments
video_directive.options = video.video_directive.options
video_directive.content = video.video_directive.content

def register_directives():
    directives.register_directive('code', code_directive)
    directives.register_directive('load-style', load_style_directive)
    directives.register_directive('page-load-style', load_style_directive)
    directives.register_directive('style', style_directive)
    directives.register_directive('page-style', style_directive)
    directives.register_directive('layout', layout_directive)
    directives.register_directive('blank', blank_directive)
    directives.register_directive('resource', resource_directive)
    directives.register_directive('interpreter', interpreter_directive)
    directives.register_directive('video', video_directive)

def gui():
    import tkFileDialog
    import tkMessageBox
    # determine which file we're displaying
    filename = tkFileDialog.askopenfilename(
        filetypes=[('ReStructuredText Files', '.rst .txt'),
                   ('All Files', '.*')],
        title='Select your presentation file to HTMLify')

    dest = re.sub('(\.rst|\.txt)', '.html', filename)
    if filename == dest:
        dest = filename + '.html'
    argv = [filename, dest]
    generate_html(argv)

    tkMessageBox.showinfo("HTML generated", "HTML written to: %s"%dest)

def main():
    '''Run either the command-line or gui interface depending on whether any
    command-line arguments were provided.
    '''
    if len(sys.argv) > 1:
        generate_html(sys.argv[1:])
    else:
        gui()

def generate_html(argv):
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

    register_directives()

    publish_cmdline(writer_name='html', argv=argv)

