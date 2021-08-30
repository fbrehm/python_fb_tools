#!/bin/bash

set -e
set -u

GITHUB_REPO_URL='https://github.com/fbrehm/python_fb_tools.git'
IMAGE_NAME="centos:8"
WORKDIR=/var/tmp/build/centos8
WORK_BRANCH="develop"
SRC_DIR=$( readlink -f $( dirname "$0" ) )
BUILD_SCRIPT="${SRC_DIR}/build-centos8-inner.sh"
CHANGELOG_SCRIPT="${SRC_DIR}/changelog-deb2rpm.py"

if type -p docker >/dev/null; then
    :
else
    echo "Command 'docker' not found."
    exit 5
fi

if [[ ! -d "${WORKDIR}" ]] ; then
    mkdir -pv "${WORKDIR}"
fi

cd "${WORKDIR}" || exit 6
if [[ -e "repo" ]] ; then
    sudo rm -rf "repo"
fi

git clone "${GITHUB_REPO_URL}" "repo"

if [[ -f .rpm-version ]] ; then
    cp -v .rpm-version repo/
fi

abort() {
    if [[ -f "${WORKDIR}/repo/.rpm-version" ]] ; then
        cp -pv "${WORKDIR}/repo/.rpm-version" "${WORKDIR}"
    fi
}

trap abort INT TERM EXIT ABRT

cd "repo"
pwd
git switch "${WORK_BRANCH}"
git branch

if [[ ! -f "${BUILD_SCRIPT}" ]] ; then
    echo "File '${BUILD_SCRIPT}' not found!"
    exit 6
fi

cp -pv "${BUILD_SCRIPT}" "build-script"
chmod -v 0755 "build-script"

if [[ ! -f "${CHANGELOG_SCRIPT}" ]] ; then
    echo "File '${CHANGELOG_SCRIPT}' not found!"
    exit 6
fi

cp -pv "${CHANGELOG_SCRIPT}" "changelog-deb2rpm"
chmod -v 0755 "changelog-deb2rpm"

docker run --hostname "$(hostname -f)" -v "${WORKDIR}":/work --workdir=/work/repo --entrypoint=./build-script "${IMAGE_NAME}"

exit 0
