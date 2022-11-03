FROM mambaorg/micromamba:git-0f27156

COPY BASE_IMAGE_LICENSE /

LABEL maintainer="conda-forge core (@conda-forge/core)"

ENV LANG en_US.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /
USER root

COPY environment.yml /tmp/environment.yml

RUN echo "**** install base env ****" && \
    micromamba install --yes --quiet --name base --file /tmp/environment.yml && \
    echo "**** cleanup ****" && \
    micromamba clean --all --force-pkgs-dirs --yes && \
    find "${MAMBA_ROOT_PREFIX}" -follow -type f \( -iname '*.a' -o -iname '*.pyc' -o -iname '*.js.map' \) -delete && \
    \
    echo "**** finalize ****" && \
    mkdir -p "${MAMBA_ROOT_PREFIX}/locks" && \
    chmod 777 "${MAMBA_ROOT_PREFIX}/locks"

COPY entrypoint /opt/docker/bin/entrypoint
RUN mkdir -p cf-autotick-bot-action
COPY / cf-autotick-bot-action/
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN cd cf-autotick-bot-action && \
    pip install -e .

ENTRYPOINT ["{MAMBA_ROOT_PREFIX}/bin/tini", "--", "/opt/docker/bin/entrypoint"]
CMD ["/bin/bash"]
