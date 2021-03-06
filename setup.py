#! /usr/bin/env python
#
# $Id$

import sys, os, zipfile, shutil

from distutils.core import setup
from distutils.cmd import Command

from bruce import __version__

# Application script file contents
LINUX_SCRIPT = '''#! /usr/bin/env python

# force module loading from my zip file first
import sys, os
zip_path = os.path.join(os.path.dirname(sys.argv[0]), 'bruce-library.zip')
sys.path.insert(0, zip_path

from bruce import %(module_name)s
%(module_name)s.main()
'''
LINUX_DESKTOP = '''[Desktop Entry]
Version=1.0
Type=Application
Name=Bruce, the Presentation Tool
Comment=The bestest Presentation Tool evah!
Exec=bruce %f
Icon=video XXX need my own icon...
MimeType=text/x-rst
'''
OSX_SCRIPT = LINUX_SCRIPT.replace('python', 'pythonw')
WINDOWS_SCRIPT = '''import sys\r
# force module loading from my zip file first\r
sys.path.insert(0, 'bruce-library.zip')\r
\r
from bruce import %(module_name)s\r
%(module_name)s.main()\r
'''

SCRIPTS = [
    ('bruce', 'run'),
    ('bruce2html', 'html_ouput'),
]

class BuildApps(Command):
    '''Special distutils command used to build the application zip files
    for the three operating systems. Also builds the examples zip file.
    '''
    description = 'Build application bundles'
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        # build the library zip file
        if not os.path.exists('build'):
            os.mkdir('build')
        if not os.path.exists('dist'):
            os.mkdir('dist')
        zipname = 'build/bruce-library.zip'
        if os.path.exists(zipname):
            os.remove(zipname)
        z = zipfile.PyZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        z.write(os.path.join('docutils-extras', 'roman.py'), 'roman.py')

        def writepy(path):
            dirlist = os.listdir(path)
            for filename in dirlist:
                filename = os.path.join(path, filename)
                if os.path.isfile(os.path.join(filename, "__init__.py")):
                    # This is a package directory, add it
                    writepy(filename)
                elif filename.endswith('.py'):
                    z.write(filename)

        for name in 'bruce pyglet cocos docutils pygments'.split():
            writepy(name)
        z.close()

        self.distribution.metadata.write_pkg_info('build')

        # zip contents shared by all
        dirname = self.distribution.get_fullname()
        def basics(zipname):
            self.distribution.dist_files.append(('sdist', '', zipname))
            z = zipfile.ZipFile(zipname, 'w')
            for file in 'bruce-library.zip PKG-INFO'.split():
                z.write('build/%s'%file, '%s/%s'%(dirname, file))

            for file in 'README.txt HOWTO.txt CHANGES.txt'.split():
                z.write(file, '%s/%s'%(dirname, file))
            return z

        # build Linux
        z = basics('dist/bruce-%s-linux.zip'%__version__)
        for script, module_name in SCRIPTS:
            open('build/%s.sh'%script, 'w').write(LINUX_SCRIPT%locals())
            os.chmod('build/%s.sh'%script, 0755)
            z.write('build/%s.sh'%script, '%s/%s.sh'%(dirname, script))
            z.close()

        # build OS X
        z = basics('dist/bruce-%s-osx.zip'%__version__)
        for script, module_name in SCRIPTS:
            open('build/%s.sh'%script, 'w').write(OSX_SCRIPT%locals())
            os.chmod('build/%s.sh'%script, 0755)
            z.write('build/%s.sh'%script, '%s/%s.sh'%(dirname, script))
            z.close()

        # build WINDOWS
        z = basics('dist/bruce-%s-windows.zip'%__version__)
        for script, module_name in SCRIPTS:
            open('build/%s.pyw'%script, 'w').write(WINDOWS_SCRIPT%locals())
            z.write('build/%s.pyw'%script, '%s/%s.pyw'%(dirname, script))
            z.close()

        # build examples
        zipname = 'dist/bruce-%s-examples.zip'%__version__
        self.distribution.dist_files.append(('sdist', '', zipname))
        z = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        dirname = 'bruce-%s-examples'%__version__
        for file in os.listdir('examples'):
            subfile = os.path.join('examples', file)
            if os.path.isfile(subfile):
                z.write(subfile, '%s/%s'%(dirname, file))
            z.write('build/PKG-INFO', '%s/PKG-INFO'%dirname)
        z.close()

# perform the setup action
setup(
    name = "bruce",
    version = __version__,
    description = "Bruce, the Presentation Tool, puts reStructuredText in your projector",
    long_description = ''.join(open('README.txt').readlines()[4:-28]),
    author = "Richard Jones",
    author_email = "richard@mechanicalcat.net",
    url = "http://r1chardj0n3s.googlepages.com/bruce",
    download_url = "http://code.google.com/p/bruce-tpt/downloads/list",
    packages = ["bruce"],
    scripts = ['scripts/bruce'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],
    cmdclass = dict(
        build_apps = BuildApps,
    ),
)

# vim: set filetype=python ts=4 sw=4 et si
