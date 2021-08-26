#!/usr/bin/python3

import sys
import os
import re
import warnings
import datetime
import textwrap

from pathlib import Path
from debian.changelog import Changelog


if len(sys.argv) < 2:
    print("Keine Changelog-Datei gegeben.", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) > 2:
    print("Zu viele Argumente übergeben.", file=sys.stderr)
    sys.exit(1)

filename = sys.argv[1]

changelog_file = Path(filename)

if not changelog_file.exists():
    print("Datei {!r} existiert nicht.".format(filename), file=sys.stderr)
    sys.exit(1)

if not changelog_file.is_file():
    print("Datei {!r} ist keine reguläre Datei.".format(filename), file=sys.stderr)
    sys.exit(1)

# print("Lese {!r} ...".format(filename), file=sys.stderr)

ch = None

re_emptyline = re.compile(r'^\s*$')
re_start_line = re.compile(r'^  \* (.*)')
re_next_line = re.compile(r'^    (.*)')

def mangle_changes(changes):

    clist = []
    change = None

    for line in changes:

        if re_emptyline.match(line):
            continue

        m = re_start_line.match(line)
        if m:
            if change:
                clist.append(change)
            change = m.group(1)
            continue

        m = re_next_line.match(line)
        if m:
            if change:
                change += ' ' + m.group(1)
            else:
                change = m.group(1)
            continue

        warnings.warn("Konnte Changelog-Entry {!r} nicht auswerten.".format(line), SyntaxWarning)

    if change:
        clist.append(change)

    return clist

with changelog_file.open('r', encoding='utf-8', errors='backslashreplace') as fh:

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ch = Changelog(fh)

        if len(w):
            print("Es gab {nr} Warnungen bein Lesen von {f!r}.".format(nr=len(w), f=filename),
                    file=sys.stderr)
            sys.exit(5)

    # print("Changelog {f!r} hat {nr} Einträge.".format(f=filename, nr=len(ch)), file=sys.stderr)

    days = {}

    for block in ch:

        lines = []
        date = datetime.datetime.strptime(block.date, '%a, %d %b %Y %H:%M:%S %z')
        day = date.strftime('%Y-%m-%d')
        # date = date.strftime('%a %b %d %Y')
        author = block.author
        version = str(block.version) + '-1'
        lines.append('*   {date} {author} {version}'.format(
            date=date, author=author, version=version))

        changes = mangle_changes(block._changes)

        if day not in days:
            days[day] = {
                    'date': date.strftime('%a %b %d %Y'),
                    'author': author,
                    'version': version,
                    'changes': changes,
            }
        else:
            for change in changes:
                days[day]['changes'].append(change)

    for day in reversed(sorted(days.keys())):
        lines = []
        block = days[day]
        lines.append('*   {date} {author} {version}'.format(
            date=block['date'], author=block['author'], version=block['version']))

        for change in block['changes']:
            for line in textwrap.wrap(
                    change, width=70, initial_indent="-   ", subsequent_indent="    "):
                lines.append(line)

        print('\n'.join(lines))

