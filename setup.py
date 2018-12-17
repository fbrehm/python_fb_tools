#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Frank Brehm
@contact: frank@brehm-online.com
@license: LGPL3+
@copyright: © 2018 Frank Brehm, Berlin
@summary: Modules for common used objects, error classes and methods.
"""
from __future__ import print_function

import os
import sys
import re
import pprint
import datetime
import textwrap
import glob
import pathlib
import subprocess

# Third party modules
from setuptools import setup
from setuptools.command.install import install

# own modules:
__base_dir__ = os.path.abspath(os.path.dirname(__file__))
__bin_dir__ = os.path.join(__base_dir__, 'bin')
__lib_dir__ = os.path.join(__base_dir__, 'lib')
__module_dir__ = os.path.join(__lib_dir__, 'fb_tools')
__init_py__ = os.path.join(__module_dir__, '__init__.py')

PATHS = {
    '__base_dir__': __base_dir__,
    '__bin_dir__': __bin_dir__,
    '__lib_dir__': __lib_dir__,
    '__module_dir__': __module_dir__,
    '__init_py__': __init_py__,
}

# -----------------------------------
def pp(obj):
    pprinter = pprint.PrettyPrinter(indent=4)
    return pprinter.pformat(obj)

#print("Paths:\n{}".format(pp(PATHS)))

if os.path.exists(__module_dir__) and os.path.isfile(__init_py__):
    sys.path.insert(0, os.path.abspath(__lib_dir__))

import fb_tools

#from fb_tools.common import pp

ENCODING = "utf-8"

__packet_version__ = fb_tools.__version__

__packet_name__ = 'fb_tools'
__debian_pkg_name__ = 'fb-tools'

__author__ = 'Frank Brehm'
__contact__ = 'frank@brehm-online.com'
__copyright__ = '(C) 2018 Frank Brehm, Berlin'
__license__ = 'LGPL3+'
__url__ = 'https://github.com/fbrehm/python_fb_tools'


__open_args__ = {}
if sys.version_info[0] < 3:
    __open_args__ = {'encoding': ENCODING, 'errors': 'surrogateescape'}

# -----------------------------------
def read(fname):

    content = None

    if sys.version_info[0] < 3:
        with open(fname, 'r') as fh:
            content = fh.read()
    else:
        with open(fname, 'r', **__open_args__) as fh:
            content = fh.read()

    return content


# -----------------------------------
def is_python_file(filename):
    if filename.endswith('.py'):
        return True
    else:
        return False


# -----------------------------------
__debian_dir__ = os.path.join(__base_dir__, 'debian')
__changelog_file__ = os.path.join(__debian_dir__, 'changelog')
__readme_file__ = os.path.join(__base_dir__, 'README.txt')


# -----------------------------------
def get_debian_version():
    if not os.path.isfile(__changelog_file__):
        return None
    changelog = read(__changelog_file__)
    first_row = changelog.splitlines()[0].strip()
    if not first_row:
        return None
    pattern = r'^' + re.escape(__debian_pkg_name__) + r'\s+\(([^\)]+)\)'
    match = re.search(pattern, first_row)
    if not match:
        return None
    return match.group(1).strip()

__debian_version__ = get_debian_version()

if __debian_version__ is not None and __debian_version__ != '':
    __packet_version__ = __debian_version__

# -----------------------------------
def write_local_version():

    local_version_file = os.path.join(__module_dir__, 'local_version.py')
    local_version_file_content = textwrap.dedent('''\
        #!/usr/bin/python
        # -*- coding: utf-8 -*-
        """
        @author: {author}
        @contact: {contact}
        @copyright: © {cur_year} by {author}, Berlin
        @summary: Modules for common used objects, error classes and methods.
        """

        __author__ = '{author} <{contact}>'
        __copyright__ = '(C) {cur_year} by {author}, Berlin'
        __contact__ = {contact!r}
        __version__ = {version!r}
        __license__ = {license!r}

        # vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
        ''')

    cur_year = datetime.date.today().year
    content = local_version_file_content.format(
        author=__author__, contact=__contact__, cur_year=cur_year,
        version=__packet_version__, license=__license__)

    if sys.version_info[0] < 3:
        with open(local_version_file, 'wt') as fh:
            fh.write(content)
    else:
        with open(local_version_file, 'wt', **__open_args__) as fh:
            fh.write(content)


# Write lib/storage_tools/local_version.py
write_local_version()

# -----------------------------------
__requirements__ = [
    'argparse',
    'six'
]


def read_requirements():

    req_file = os.path.join(__base_dir__, 'requirements.txt')
    if not os.path.isfile(req_file):
        return

    f_content = read(req_file)
    if not f_content:
        return

    re_comment = re.compile(r'\s*#.*')
    re_module = re.compile(r'([a-z][a-z0-9_]*[a-z0-9])', re.IGNORECASE)

    for line in f_content.splitlines():
        line = line.strip()
        line = re_comment.sub('', line)
        if not line:
            continue
        match = re_module.search(line)
        if not match:
            continue
        module = match.group(1)
        if module not in __requirements__:
            __requirements__.append(module)

    #print("Found required modules: {}\n".format(pp(__requirements__)))


read_requirements()

# -----------------------------------
__scripts__ = []

def get_scripts():

    fpattern = os.path.join(__bin_dir__, '*')
    for fname in glob.glob(fpattern):
        script_name = os.path.relpath(fname, __base_dir__)
        if not os.path.isfile(fname):
            continue
        if not os.access(fname, os.X_OK):
            continue

        if script_name not in __scripts__:
            __scripts__.append(script_name)

    #print("Found scripts: {}\n".format(pp(__scripts__)))


get_scripts()

# -----------------------------------
__locale_files__ = {}
__data__files__ = []

def is_locale_file(filename):
    if filename.endswith('.po') or filename.endswith('.mo'):
        return True
    else:
        return False

def get_locales():

    if hasattr(sys, 'real_prefix'):
        print("Real prefix: {!r}".format(sys.real_prefix))
        share_prefix = os.path.join(sys.real_prefix, 'share')
    else:
        share_prefix = os.path.join(sys.prefix, 'share')
    share_prefix  = os.sep + 'share'
    print("Share prefix: {!r}.".format(share_prefix))
    for root, dirs, files in os.walk('locale'):
        if files:
            for f in filter(is_locale_file, files):
                if root not in __locale_files__:
                    __locale_files__[root] = []
                loc_file = os.path.join(root, f)
                __locale_files__[root].append(loc_file)

    #print("Found locale files: {}\n".format(pp(__locale_files__)))

    for root in sorted(__locale_files__.keys()):
        target = os.path.join(share_prefix, root)
        __data__files__.append((target, __locale_files__[root]))

    #print("Found data files: {}\n".format(pp(__data__files__)))


get_locales()

MO_FILES = 'locale/*/LC_MESSAGES/*.mo'
PO_FILES = 'locale/*/LC_MESSAGES/*.po'

def create_mo_files():
    mo_files = []
    for po_path in glob.glob(PO_FILES):
        mo = pathlib.Path(po_path.replace('.po', '.mo'))
        if not mo.exists():
            subprocess.call(['msgfmt', '-o', str(mo), po_path])
            #subprocess.run(['msgfmt', '-o', str(mo), po_path], check=True)
        mo_files.append(str(mo))

    print("Found mo files: {}\n".format(pp(mo_files)))
    return mo_files


# -----------------------------------
class InstallWithCompile(install, object):
    def run(self):
        from babel.messages.frontend import compile_catalog
        compiler = compile_catalog(self.distribution)
        option_dict = self.distribution.get_option_dict('compile_catalog')
        compiler.domain = [option_dict['domain'][1]]
        compiler.directory = option_dict['directory'][1]
        compiler.statistics = bool(option_dict['statistics'][1])
        compiler.run()
        super(InstallWithCompile, self).run()


# -----------------------------------
setup(
    version=__packet_version__,
    long_description=read('README.md'),
    scripts=__scripts__,
    requires=__requirements__,
    #data_files=__data__files__,
    package_dir={'': 'lib'},
    cmdclass={
        'install': InstallWithCompile,
    },
    package_data = {
        '': create_mo_files(),
    },
)


# =======================================================================

# vim: fileencoding=utf-8 filetype=python ts=4 expandtab
