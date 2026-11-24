# syntax=docker/dockerfile:1.7
#
# Commit image for ansible-core (pure Python, Atheris/libFuzzer targets). Built on the org base,
# which ships CPython 3.13 (ansible-core devel needs >=3.13), pip, clang and libcrypt1 (ansible's
# crypt facade loads libcrypt via ctypes; used by the fuzz_encrypt target).
#
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile --build-arg COMMIT=$(git rev-parse HEAD) -t ansible .
FROM ghcr.io/savantenvs/base:20261023

ARG COMMIT
ARG REPO_URL
ARG SOURCE_DATE_EPOCH
ARG SANITIZER_FLAGS
ARG MAYHEM_JOBS=

# Python deps live at a fixed, $HOME-independent prefix (wheelhouse + site dir) so the air-gapped
# PATCH re-run of build.sh resolves them; ansible itself is the source tree at /mayhem/lib.
ENV PY_PREFIX=/opt/toolchains/python \
    PYTHONPATH=/opt/toolchains/python/site:/mayhem/lib \
    PYTHONDONTWRITEBYTECODE=1
USER root
RUN install -d -o 2000 -g 2000 /opt/toolchains/python
USER mayhem

WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

RUN bash mayhem/build.sh
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
