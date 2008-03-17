import os
import pyglet
from bruce import page
from bruce import config

loader = pyglet.resource.Loader(path=[])

class Resource(page.NoContent):
    name = 'resource'

    def __init__(self, content, **kw):
        super(Resource, self).__init__(content, **kw)

        for line in self.content.splitlines():
            line = line.strip()
            if not os.path.isabs(line):
                line = os.path.join(config.get('directory'), line)
            if line.lower().endswith('.ttf'):
                pyglet.font.add_file(line)
            else:
                loader.path.append(line)
        loader.reindex()
        return None
