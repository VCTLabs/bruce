
try:
    import pygments
    from pygments import token, lexers, util
    from pygments.formatter import Formatter
    have_pygments = True
except ImportError:
    have_pygments = False
    Formatter=object

class BruceFormatter(Formatter):
    def __init__(self, generator):
        self.generator = generator

    def format(self, tokensource, outfile):
        generator = self.generator
        for ttype, value in tokensource:
            if not value: continue
            style = ['code'] + [s.lower() for s in ttype]
            while 1:
                name = '_'.join(style)
                if name in generator.stylesheet:
                    style = generator.stylesheet[name]
                    break
                style.pop()
            marker = []
            generator.push_style(marker, style)
            value = value.replace('\n', u'\u2028')
            generator.add_text(value)
            generator.pop_style(marker)

def handle_rst_node(generator, node, lexer_name=None):
    text = node.astext()
    if lexer_name is None:
        if 'langauge' in node:
            lexer_name = node['language']
        else:
            try:
                lexer_name = lexers.guess_lexer(text)
            except util.ClassNotFound:
                # what the hell, it might be...
                lexer_name = 'python'

    # parse the text
    lexer = lexers.get_lexer_by_name(lexer_name)
    tokens = lexer.get_tokens(node.astext())

    # format according to Bruce
    formatter = BruceFormatter(generator)
    formatter.format(tokens, None)

