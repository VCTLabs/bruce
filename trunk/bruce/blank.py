import os

from bruce import config
from bruce import page

class BlankPage(page.Page):
    name = 'blank'

    @classmethod
    def as_html(cls, content, **config):
        return ''

    def draw(self):
        pass

#config.add_section('blank', {})
