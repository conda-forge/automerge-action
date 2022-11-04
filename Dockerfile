FROM mambaorg/micromamba:git-0f27156 AS build-env

ENV PYTHONDONTWRITEBYTECODE=1
USER root

COPY conda-lock.yml /tmp/conda-lock.yml

RUN echo "**** install base env ****" && \
    micromamba install --yes --quiet --name base --file /tmp/conda-lock.yml
RUN echo "**** cleanup ****" && \
    micromamba clean --all --force-pkgs-dirs --yes && \
    find "${MAMBA_ROOT_PREFIX}" -follow -type f \( -iname '*.a' -o -iname '*.pyc' -o -iname '*.js.map' \) -delete
RUN echo "**** finalize ****" && \
    mkdir -p "${MAMBA_ROOT_PREFIX}/locks" && \
    chmod 777 "${MAMBA_ROOT_PREFIX}/locks"

FROM frolvlad/alpine-glibc:alpine-3.16_glibc-2.34

COPY --from=build-env /opt/conda /opt/conda

COPY BASE_IMAGE_LICENSE /

LABEL maintainer="conda-forge core (@conda-forge/core)"

ENV LANG en_US.UTF-8

ARG CONDA_DIR="/opt/conda"

ENV PATH="$CONDA_DIR/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p cf-autotick-bot-action
COPY / cf-autotick-bot-action/
RUN cd cf-autotick-bot-action && \
    pip install -e .

COPY entrypoint /opt/docker/bin/entrypoint
ENTRYPOINT ["/opt/conda/bin/tini", "--", "/opt/docker/bin/entrypoint"]
