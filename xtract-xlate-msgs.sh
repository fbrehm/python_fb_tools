#!/bin/bash

set -e
set -u

base_dir=$( dirname $0 )
cd ${base_dir}

locale_dir=locale
locale_domain="fb_tools"
pot_file="${locale_dir}/${locale_domain}.pot"
po_with=99
my_address="${DEBEMAIL:-frank@brehm-online.com}"

pkg_version=$( cat debian/changelog | head -n 1 | sed -e 's/^[^(]*(//' -e 's/).*//' )

pybabel extract bin/* lib \
    -o "${pot_file}" \
    -F etc/babel.ini \
    --keyword="_" --keyword="__" \
    --width=${po_with} \
    --sort-by-file \
    --msgid-bugs-address="${my_address}" \
    --copyright-holder="Frank Brehm, Berlin" \
    --project="${locale_domain}" \
    --version="${pkg_version}"

for lang in de_DE en_US ; do
    if [[ ! -f "${locale_dir}/${lang}/LC_MESSAGES/${locale_domain}.po" ]] ; then
        pybabel init --domain "${locale_domain}" \
            --input-file "${pot_file}" \
            --output-dir "${locale_dir}" \
            --locale "${lang}" \
            --width ${po_with}
    else
        pybabel update --domain "${locale_domain}" \
            --input-file "${pot_file}" \
            --output-dir "${locale_dir}" \
            --locale "${lang}" \
            --width ${po_with} \
            --ignore-obsolete \
            --update-header-comment
    fi
done

