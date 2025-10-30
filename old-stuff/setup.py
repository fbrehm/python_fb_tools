#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@summary: Modules for common used objects, error classes and methods.

@author: Frank Brehm
@contact: frank@brehm-online.com
@license: LGPL3+
@copyright: © 2025 Frank Brehm, Berlin
"""
from __future__ import print_function

import datetime
import os
import pprint
import re
import subprocess
import sys
import textwrap
from pathlib import Path

# own modules:

__base_dir__ = Path(os.path.abspath(os.path.dirname(__file__)))
__bin_dir__ = __base_dir__ / 'bin'
__lib_dir__ = __base_dir__ / 'lib'
__module_dir__ = __lib_dir__ / 'fb_tools'
__init_py__ = __module_dir__ / '__init__.py'
__local_usr_dir__ = __base_dir__ / 'usr'
__share_dir__ = Path(sys.base_prefix) / 'share'
__local_share_dir__ = Path(str(__base_dir__) + str(__share_dir__)).relative_to(__base_dir__)
__man_dir__ = Path('share/man')
__local_man_dir__ = __local_share_dir__ / 'man'
__man1_dir__ = __man_dir__ / 'man1'
__local_man1_dir__ = __local_man_dir__ / 'man1'
__locale_dir__ = Path('share/locale')
__local_locale_dir__ = __base_dir__ / 'locale'

__debian_dir__ = __base_dir__ / 'debian'
__changelog_file__ = __debian_dir__ / 'changelog'
__readme_file__ = __base_dir__ / 'README.md'

PATHS = {
    '__base_dir__': __base_dir__,
    '__bin_dir__': __bin_dir__,
    '__lib_dir__': __lib_dir__,
    '__module_dir__': __module_dir__,
    '__init_py__': __init_py__,
    '__local_usr_dir__': __local_usr_dir__,
    '__share_dir__': __share_dir__,
    '__local_share_dir__': __local_share_dir__,
    '__locale_dir__': __locale_dir__,
    '__man_dir__': __man_dir__,
    '__man1_dir__': __man1_dir__,
    '__local_man_dir__': __local_man_dir__,
    '__local_man1_dir__': __local_man1_dir__,
    '__debian_dir__': __debian_dir__,
    '__changelog_file__': __changelog_file__,
    '__readme_file__': __readme_file__,
    '__local_locale_dir__': __local_locale_dir__,
}

__verbose__ = False


# -----------------------------------
def pp(obj):
    """Return a pretty print string of the given value."""
    pprinter = pprint.PrettyPrinter(indent=4)
    return pprinter.pformat(obj)


if __verbose__:
    print('Paths:\n{}'.format(pp(PATHS)))

if __module_dir__.exists() and __init_py__.is_file():
    sys.path.insert(0, str(__lib_dir__))

# Third party modules
from babel.messages import frontend as babel

import fb_tools

from setuptools import setup
from setuptools.command.sdist import sdist

# from fb_tools.common import pp

ENCODING = 'utf-8'

__packet_version__ = fb_tools.__version__

__packet_name__ = 'fb_tools'
__debian_pkg_name__ = 'fb-tools'

__author__ = 'Frank Brehm'
__contact__ = 'frank@brehm-online.com'
__copyright__ = '(C) 2025 Frank Brehm, Berlin'
__license__ = 'LGPL3+'
__url__ = 'https://github.com/fbrehm/python_fb_tools'


__open_args__ = {'encoding': ENCODING, 'errors': 'surrogateescape'}

# -----------------------------------
def read(file2read):
    """Read the given file and return its content."""
    content = None

    with file2read.open('r', **__open_args__) as fh:
        content = fh.read()

    return content


# -----------------------------------
def is_python_file(file2inspect):
    """Return, whether the given file seems to be a Python source file."""
    if file2inspect.suffix == '.py':
        return True
    else:
        return False


# -----------------------------------
def get_debian_version():
    """Return the latest package version fron Debian changelog file."""
    if not __changelog_file__.is_file():
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
    """Write the local version file."""
    local_version_file = __module_dir__ / 'local_version.py'
    local_version_file_content = textwrap.dedent('''\
        #!/usr/bin/python
        # -*- coding: utf-8 -*-
        """
        @summary: Modules for common used objects, error classes and methods.

        @author: {author}
        @contact: {contact}
        @copyright: © {cur_year} by {author}, Berlin
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

    with local_version_file.open('wt', **__open_args__) as fh:
        fh.write(content)


# Write lib/storage_tools/local_version.py
write_local_version()

# -----------------------------------
__requirements__ = [
    'argparse',
    'six'
]

# -----------------------------------
def read_requirements():
    """Read the requiremments.txt file."""
    req_file = __base_dir__ / 'requirements.txt'
    if not req_file.is_file():
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

    if __verbose__:
        print('Found required modules: {}\n'.format(pp(__requirements__)))


read_requirements()

# -----------------------------------
__scripts__ = []

def get_scripts():
    """Collect binary script files from bin/."""
    for script in __bin_dir__.glob('*'):
        script_rel = str(script.relative_to(__base_dir__))
        if not script.is_file():
            continue
        if not os.access(str(script), os.X_OK):
            continue

        if script_rel not in __scripts__:
            __scripts__.append(script_rel)

    if __verbose__:
        print('Found scripts: {}\n'.format(pp(__scripts__)))


get_scripts()

# -----------------------------------
__data_files__ = []

re_usr = re.compile(r'^usr/')
re_man = re.compile(r'man/man\S+$')

if __local_usr_dir__.is_dir():
    usr_files = {}
    for f in __local_usr_dir__.glob('**/*'):
        if f.is_file():
            relpath = Path(os.path.relpath(str(f), __base_dir__))
            reldir = re_usr.sub('', str(relpath.parent))
            # if re_man.search(str(reldir)):
            #     continue
            if str(reldir) not in usr_files:
                usr_files[str(reldir)] = []
            usr_files[str(reldir)].append(str(relpath))
    for udir in usr_files.keys():
        __data_files__.append((udir, usr_files[udir]))

if __verbose__:
    print('Found data files:\n' + pp(__data_files__) + '\n')

# -----------------------------------
# PO_FILES = 'locale/*/LC_MESSAGES/*.po'
# __package_data__ = {}

def create_mo_files():
    """Compile the translation files."""
    mo_files = []
    for po_path in __local_locale_dir__.glob('**/*.po'):
        po_path_rel = po_path.relative_to(__base_dir__)
        mo_path = po_path_rel.with_suffix('.mo')
        if not mo_path.exists():
            subprocess.call(['msgfmt', '-o', str(mo_path), str(po_path)])
        mo_files.append(mo_path)

    if __verbose__:
        print('Found mo files: {}\n'.format(pp(mo_files)))
    return mo_files


__pkg_mo_paths__ = create_mo_files()
__pkg_mo_files__ = []
for mo_file in __pkg_mo_paths__:
    __pkg_mo_files__.append(str(mo_file))

for mo_file in __pkg_mo_paths__:
    ltype = mo_file.parent.name
    lname = mo_file.parent.parent.name
    ldir = __locale_dir__ / lname / ltype
    mo_file_rel = str(mo_file).lstrip('/')
    __data_files__.append((str(ldir), [mo_file_rel]))

if __verbose__:
    print('Found data files:\n' + pp(__data_files__) + '\n')

# -----------------------------------
class Sdist(sdist):
    """Custom ``sdist`` command to ensure that mo files are always created."""

    def run(self):
        """Compile the l18n catalog."""
        self.run_command('compile_catalog')
        # sdist is an old style class so super cannot be used.
        sdist.run(self)


# -----------------------------------
setup(
    version=__packet_version__,
    long_description=read(__readme_file__),
    scripts=__scripts__,
    requires=__requirements__,
    package_dir={'': 'lib'},
    data_files=__data_files__,
    cmdclass={
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog,
        'sdist': Sdist,
    },
)


# =======================================================================

# vim: fileencoding=utf-8 filetype=python ts=4 expandtab
