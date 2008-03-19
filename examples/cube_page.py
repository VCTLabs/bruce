import ctypes

from pyglet.gl import *

from bruce import page
from bruce import config

def render_cube():
    glBegin(GL_TRIANGLES)
    glNormal3f(+1.0, 0.0, 0.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, -1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(+1.0, -1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);

    glNormal3f(0.0, +1.0, 0.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, -1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);

    glNormal3f(0.0, 0.0, +1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0); glVertex3f(-1.0, -1.0, +1.0)
    glVertex3f(+1.0, +1.0, +1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0);

    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(-1.0, +1.0, +1.0);
    glVertex3f(-1.0, +1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, +1.0, +1.0);

    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, +1.0); glVertex3f(+1.0, -1.0, +1.0);
    glVertex3f(+1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(+1.0, -1.0, +1.0);

    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0); glVertex3f(-1.0, +1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);
    glVertex3f(+1.0, -1.0, -1.0); glVertex3f(-1.0, -1.0, -1.0); glVertex3f(+1.0, +1.0, -1.0);
    glEnd()

def cube_list():
    cube_dl = glGenLists(1)
    glNewList(cube_dl, GL_COMPILE)
    render_cube()
    glEndList()
    return cube_dl

def cube_array_list():
    cubes_dl = glGenLists(1)
    glNewList(cubes_dl, GL_COMPILE)
    glMatrixMode(GL_MODELVIEW)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)
    glPushMatrix()
    for x in range(-10, +11, +2):
        for y in range(-10, +11, +2):
            for z in range(-10, +11, +2):
                glPushMatrix()
                glTranslatef(x * 2.0, y * 2.0, z * 2.0)
                glScalef(.8, .8, .8)
                glColor4f((x + 10.0) / 20.0, (y + 10.0) / 20.0,
                    (z + 10.0) / 20.0, 1.0)
                render_cube()
                glPopMatrix()
    glPopMatrix()
    glDisable(GL_COLOR_MATERIAL)
    glEndList()
    return cubes_dl


class Page(page.Page):
    name = 'cube'

    def on_enter(self, vw, vh):
        self.cube = cube_list()
        self.r = 0
        fourfv = ctypes.c_float * 4
        glLightfv(GL_LIGHT0, GL_POSITION, fourfv(100, 200, 200, 0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, fourfv(0.5, 0.5, 0.5, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, fourfv(0.8, 0.8, 0.8, 1.0))
        self.on_resize(vw, vh)

    def on_leave(self):
        glDeleteLists(self.cube, 1)
        self.cube = None

    def update(self, dt):
        self.r += 90 * dt
        if self.r > 360: self.r -= 360

    def on_resize(self, vw, vh):
        self.viewport = (vw, vh)

    def draw(self):
        glPushAttrib(GL_LIGHTING_BIT|GL_ENABLE_BIT|GL_CURRENT_BIT)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glColor4f(*[n/255. for n in self.cfg['color']])


        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        vw, vh = self.viewport
        gluPerspective(60., float(vw)/vh, 1., 100.)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(3, 3, 3, 0, 0, 0, 0, 1, 0)
        glRotatef(self.r, 1, 0, 0)
        glRotatef(self.r/2, 0, 1, 0)
        glCallList(self.cube)
        glPopMatrix()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glMatrixMode(GL_MODELVIEW)

        glPopAttrib()

config.add_section('cube', (('color', tuple, (255, 255, 255, 255)),))

