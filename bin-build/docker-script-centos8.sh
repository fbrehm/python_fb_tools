#!/bin/bash

set -e
set -u
set -x

hostname -f
whoami
pwd
echo
locale -a
dnf clean all && dnf makecache
dnf --assumeyes install langpacks-en glibc-all-langpacks
locale -a
locale
export LC_ALL=en_US.utf8
locale
dnf --assumeyes install epel-release
dnf makecache
dnf --assumeyes upgrade

dnf --assumeyes module enable python36
dnf --assumeyes module enable python38

dnf --assumeyes install \
    python3-debian \
    python36 \
    python38 \
    python38-setuptools \
    python38-pip \
    python38-devel \
    python38-pytz \
    python38-six \
    python38-babel \
    platform-python-devel \
    gnupg2 \
    rpm-build \
    tree \
    expect \
    gettext

ls -l --color=always /bin/python* /bin/pip* || true
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

cat specs/fb_tools.el8.spec.template | \
    sed -e "s/@@@Version@@@/$PKG_VERSION/gi" \
        -e "s/@@@Release@@@/${PKG_RELEASE}/gi" > specs/fb_tools.spec

python3.6 changelog-deb2rpm debian/changelog >>specs/fb_tools.spec
echo >> specs/fb_tools.spec
echo '# vim: filetype=spec' >>specs/fb_tools.spec

sleep 1

