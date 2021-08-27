#!/bin/bash

set -e
set -u

hostname -f
whoami
pwd
echo
locale -a
yum clean all && yum makecache

for l in de_AT de_CH de_DE en_CA en_GB en_IE en_IN en_US ; do
    echo "${l}.utf8"
    localedef --charmap UTF-8 --inputfile "${l}" "${l}.utf8"
done

locale -a
locale
export LC_ALL=en_US.utf8
locale
yum --assumeyes install epel-release
yum makecache
yum --assumeyes upgrade

yum --assumeyes install \
    python \
    python-devel \
    python-pathlib \
    python-debian \
    python2-pip \
    python-setuptools \
    python-babel \
    python-ipaddress \
    python-six \
    pytz \
    python36 \
    python36-pip \
    python36-devel \
    python36-pytz \
    python36-babel \
    python36-six \
    gnupg2 \
    rpm-build \
    tree \
    gettext


echo "I want this bloody foolish package python36-babel!!!1!1!!"
yum --assumeyes install python36-babel

ls -l --color=always /bin/python* /bin/pip* || true
pip2 list
pip3 list

echo "--------------------------------------"

mkdir -pv rpmdir
mkdir -pv rpmdir/SOURCES
ODIR=$(pwd)
ROOT_OBJECTS=$( ls -A1 | egrep -vw ".git|rpmdir" )
PKG_VERSION=$( ./get-rpm-version )
PKG_RELEASE=$( ./get-rpm-release )
echo "Version to build: ${PKG_VERSION}-${PKG_RELEASE}"
mkdir -pv "rpmdir/SOURCES/python_fb_tools-${PKG_VERSION}"

tar cf - ${ROOT_OBJECTS} | (cd "rpmdir/SOURCES/python_fb_tools-${PKG_VERSION}" ; tar xf -)
cd rpmdir/SOURCES && tar cfz "fb_tools.${PKG_VERSION}.tar.gz" "python_fb_tools-${PKG_VERSION}"
ls -lA --color=always
cd "${ODIR}"

cat specs/fb_tools.el7.template.spec | \
    sed -e "s/@@@Version@@@/$PKG_VERSION/gi" \
        -e "s/@@@Release@@@/${PKG_RELEASE}/gi" > specs/fb_tools.spec

python2 bin-build/changelog-deb2rpm.py debian/changelog >>specs/fb_tools.spec

rpmbuild -ba --nocheck --verbose \
    --define "_topdir $(pwd)/rpmdir" \
    --define "version ${PKG_VERSION}" \
    --define "python3_version_nodots 36" \
    specs/fb_tools.spec

tree -aQpugs rpmdir/*RPMS || true
tree -aQpugs rpmdir/*RPMS || true
ls -lA rpmdir/RPMS/*/* rpmdir/SRPMS/*

echo "${PKG_VERSION}-${PKG_RELEASE}" > .rpm-version

