FROM docker.io/lavasoftware/lava-dispatcher:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install --yes podman && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY docker /usr/bin/docker

ENTRYPOINT ["/root/entrypoint.sh"]
