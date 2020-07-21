#!bin/bash

# Clear out the /build and /release directory
rm -rf /build/*
rm -rf /release/*

# Re-pull the repository
git fetch && \
    BUILD_VERSION=$(git describe --tags $(git rev-list --tags --max-count=1)) && \
    git checkout "${BUILD_VERSION}"

DISTRIBUTOR=$( lsb_release --short --id )
OS_CODENAME=$( lsb_release --short --codename )
OS_RELEASE=$( lsb_release --short --release )

export DEBFULLNAME="Frank Brehm"
export DEBEMAIL="frank@brehm-online.com"
BUILDER="${DEBFULLNAME} <${DEBEMAIL}>"

if [[ "$#" -ge 1 ]] ; then
    VERSION_PREFIX="$1"
else
    if [[ "${DISTRIBUTOR}" =~ Debian ]] ; then
        VERSION_PREFIX="deb${OS_RELEASE}"
    elif [[ "${DISTRIBUTOR}" =~ Ubuntu ]] ; then
        VERSION_PREFIX="ubuntu${OS_RELEASE}"
    elif [[ "${DISTRIBUTOR}" =~ LinuxMint ]] ; then
        VERSION_PREFIX="mint${OS_RELEASE}"
    else
        VERSION_PREFIX="$( echo "${DISTRIBUTOR}" | tr '[:upper:]' '[:lower:]' )${OS_RELEASE}"
    fi
fi

BUILD_VERSION="${BUILD_VERSION}~${VERSION_PREFIX}"

# debchange --newversion "${BUILD_VERSION}" \
#     --distribution "${OS_CODENAME}" \
#     --urgency medium \
#     "Build for ${DISTRIBUTOR} ${OS_RELEASE} - ${OS_CODENAME}"

dpkg-buildpackage --build all --no-sign \
    -v"${BUILD_VERSION}" \
    -C"Build for ${DISTRIBUTOR} ${OS_RELEASE} - ${OS_CODENAME}" \
    --release-by "${BUILDER}" \
    --build-by "${BUILDER}"

echo "Current directory: $( pwd )"
echo "Parent directory:"
ls -l -d --color=always ..

cp -pv ../*.deb ../*.dsc ../*.tar* /pkgs

