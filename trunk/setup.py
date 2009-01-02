#! /usr/bin/env python
#
# $Id$

import sys, os, zipfile, shutil

from distutils.core import setup
from distutils.cmd import Command

from bruce import __version__

class BuildLibs(Command):
    '''Build the zip file with the library contents for all of Bruce and its
    dependencies. Not really to be invoked by itself but rather as part of
    the application build.
    '''
    description = 'Build library bundle for applications'
    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        zipname = 'build/bruce-library-%s%s.zip'%sys.version_info[:2]
        if os.path.exists(zipname):
            os.remove(zipname)
        z = zipfile.PyZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        z.write(os.path.join('docutils-extras', 'roman.py'), 'roman.py')
        for name in 'bruce pyglet cocos docutils pygments'.split():
            z.writepy(name)
        z.close()
        return zipname

# Application script file contents
LINUX_SCRIPT = '''#! /usr/bin/env python

import sys
# force module loading from my zip file first
sys.path.insert(0, 'bruce-library-%s%s.zip'%sys.version_info[:2])

from bruce import run
run.main()
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
sys.path.insert('bruce-library-%s%s.zip'%sys.version_info[:2])\r
\r
from bruce import run\r
run.main()\r
'''

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
        # need to generate a zipfile for 2.5 and 2.6 :(
        # shell out anyway so we generate the .pyo file
        os.system('python2.5 -O setup.py build_libs')
        os.system('python2.6 -O setup.py build_libs')

        # remember the archive filenames generated for later distutils commands
        # (ie. upload)
        self.archive_files = []

        # zip contents shared by all
        dirname = 'bruce-%s'%__version__
        def basics(zipname):
            self.archive_files.append(zipname)
            z = zipfile.ZipFile(zipname, 'w')
            for version in '25 26'.split():
                n = 'bruce-library-%s.zip'%version
                z.write('build/%s'%n, '%s/%s'%(dirname, n))

            for file in 'README.txt HOWTO.txt CHANGES.txt'.split():
                z.write(file, '%s/%s'%(dirname, file))
            return z

        # build Linux
        z = basics('build/bruce-%s-linux.zip'%__version__)
        open('build/bruce.sh', 'w').write(LINUX_SCRIPT)
        os.chmod('build/bruce.sh', 0755)
        z.write('build/bruce.sh', '%s/bruce.sh'%(dirname, ))
        z.close()

        # build OS X
        z = basics('build/bruce-%s-osx.zip'%__version__)
        open('build/bruce.sh', 'w').write(OSX_SCRIPT)
        os.chmod('build/bruce.sh', 0755)
        z.write('build/bruce.sh', '%s/bruce.sh'%(dirname, ))
        z.close()

        # build WINDOWS
        z = basics('build/bruce-%s-windows.zip'%__version__)
        open('build/bruce.pyw', 'w').write(WINDOWS_SCRIPT)
        z.write('build/bruce.pyw', '%s/bruce.pyw'%(dirname, ))
        z.close()

        # build examples
        zipname = 'build/bruce-%s-examples.zip'%__version__
        self.archive_files.append(zipname)
        z = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED)
        dirname = 'bruce-%s-examples'%__version__
        for file in os.listdir('examples'):
            subfile = os.path.join('examples', file)
            if os.path.isfile(subfile):
                z.write(subfile, '%s/%s'%(dirname, file))
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
        build_libs = BuildLibs,
    ),
)

# vim: set filetype=python ts=4 sw=4 et si
