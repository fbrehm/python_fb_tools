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
dnf --assumeyes install \
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

sleep 1

