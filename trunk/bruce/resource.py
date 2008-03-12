import os
import pyglet
from bruce import page
from bruce import config

loader = pyglet.resource.Loader(path=[])

class Resource(page.Page):

    @classmethod
    def as_page(cls, content, **kw):
        for line in content.splitlines():
            line = line.strip()
            if not os.path.isabs(line):
                line = os.path.join(config.get('directory'), line)
            if line.lower().endswith('.ttf'):
                pyglet.font.add_file(line)
            else:
                loader.path.append(line)
        loader.reindex()
        return None

