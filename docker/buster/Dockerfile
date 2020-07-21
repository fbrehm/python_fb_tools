
FROM debian:buster
MAINTAINER Frank Brehm <frank@brehm-online.com>

# Volumes
VOLUME /pkgs
# VOLUME /release

# Install build dependencies
RUN apt-get update && apt-get -y install --no-install-recommends \
    build-essential \
    devscripts \
    fakeroot \
    debhelper \
    automake \
    autotools-dev \
    pkg-config \
    git \
    gettext \
    help2man \
    lsb-release \
    ca-certificates

# Install application dependencies
RUN apt-get -y install --no-install-recommends \
    python-all \
    python-argparse \
    python-babel \
    python-setuptools \
    python-pathlib \
    python-pip \
    python-six \
    python-tz \
    python3-all \
    python3-babel \
    python3-pip \
    python3-setuptools \
    python3-six \
    python3-tz \
    dh-python
    
RUN mkdir /src
RUN git clone https://github.com/fbrehm/python_fb_tools.git /src/fb_tools
WORKDIR /src/fb_tools
RUN git fetch

# Import resources
COPY entrypoint.sh /entrypoint.sh

# Make Executable
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh", "deb10"]

# vim: filetype=dockerfile
