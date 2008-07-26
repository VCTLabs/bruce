
try:
    import pygments
    from pygments import token, lexers
    have_pygments = True
except ImportError:
    have_pygments = False

from pygments.formatter import Formatter

class BruceFormatter(Formatter):
    def __init__(self, generator):
        self.generator = generator

    def format(self, tokensource, outfile):
        generator = self.generator
        for ttype, value in tokensource:
            if not value: continue
            style = generator.stylesheet['code_%s'%ttype[0].lower()]
            marker = []
            generator.push_style(marker, style)
            value = value.replace('\n', u'\u2028')
            generator.add_text(value)
            generator.pop_style(marker)

def handle_rst_node(generator, node, lexer_name=None):
    if lexer_name is None:
        # get name from node
        lexer_name = node.get('language', 'python')
    lexer = lexers.get_lexer_by_name(lexer_name)
    tokens = lexer.get_tokens(node.astext())
    formatter = BruceFormatter(generator)
    formatter.format(tokens, None)

