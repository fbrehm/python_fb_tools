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

# Because of python36-babel
#     - 'echo -e "[pixelpark]\nname=pixelpark\nbaseurl=https://${YUM_REPO_HOST}${YUM_REPO_DIR_HTTP}/7/\nenabled=1\ngpgcheck=1\ngpgkey=https://repo01.pixelpark.com/gpg/pixelpark.gpg" > /etc/yum.repos.d/pixelpark.repo'
cat > /etc/yum.repos.d/pixelpark.repo <<- EOF
	[pixelpark]
	name=pixelpark
	baseurl=https://repo01.pixelpark.com/Linux/yum/pixelpark/7/
	enabled=1
	gpgcheck=1
	gpgkey=https://repo01.pixelpark.com/gpg/pixelpark.gpg
	EOF

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
    python36-packaging \
    python36-babel \
    python36-six \
    gnupg2 \
    rpm-build \
    tree \
    gettext


# echo "I want this bloody foolish package python36-babel!!!1!1!!"
# yum --assumeyes install python36-babel

ls -l --color=always /bin/python* /bin/pip* || true
pip2 list
pip3 list

echo "--------------------------------------"

mkdir -pv rpmdir
mkdir -pv rpmdir/SOURCES
ODIR=$(pwd)
ROOT_OBJECTS=$( find ./.[^.]* ./* -maxdepth 0 | grep -E -vw ".git|rpmdir" | sed -e 's|^\./||' )
PKG_VERSION=$( ./get-rpm-version )
PKG_RELEASE=$( ./get-rpm-release )
echo "Version to build: ${PKG_VERSION}-${PKG_RELEASE}"
mkdir -pv "rpmdir/SOURCES/python_fb_tools-${PKG_VERSION}"

tar cf - "${ROOT_OBJECTS}" | (cd "rpmdir/SOURCES/python_fb_tools-${PKG_VERSION}" ; tar xf -)
cd rpmdir/SOURCES && tar cfz "fb_tools.${PKG_VERSION}.tar.gz" "python_fb_tools-${PKG_VERSION}"
ls -lA --color=always
cd "${ODIR}"

# cat specs/fb_tools.el7.template.spec | \
sed -e "s/@@@Version@@@/$PKG_VERSION/gi" \
    -e "s/@@@Release@@@/${PKG_RELEASE}/gi" \
    specs/fb_tools.el7.template.spec > specs/fb_tools.spec

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

