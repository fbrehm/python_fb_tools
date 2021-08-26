#!/bin/bash

set -e
set -u

GITHUB_REPO_URL='https://github.com/fbrehm/python_fb_tools.git'
IMAGE_NAME="centos:8"
WORKDIR=/var/tmp/build/centos8
WORK_BRANCH="develop"
SRC_DIR=$( readlink -f $( dirname "$0" ) )
DOCKER_SRCIPT="${SRC_DIR}/docker-script-centos8.sh"

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
    rm -rf "repo"
fi

git clone "${GITHUB_REPO_URL}" "repo"
cd "repo"
pwd
git switch "${WORK_BRANCH}"
git branch

if [[ ! -f "${DOCKER_SRCIPT}" ]] ; then
    echo "File '${DOCKER_SRCIPT}' not found!"
    exit 6
fi

cp -pv "${DOCKER_SRCIPT}" "docker-script"
chmod -v 0755 "docker-script"

docker run --hostname "$(hostname -f)" -v "${WORKDIR}":/work --workdir=/work/repo --entrypoint=./docker-script "${IMAGE_NAME}"

exit 0
