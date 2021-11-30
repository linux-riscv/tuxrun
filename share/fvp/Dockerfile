FROM docker.io/lavasoftware/lava-dispatcher:2021.11

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends --yes gnupg && \
    echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_11/ /" > /etc/apt/sources.list.d/kubic.list && \
    curl -L "https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_11/Release.key" | apt-key add - && \
    apt-get update && \
    apt-get install --yes podman && \
    apt-get purge --yes gnupg && \
    apt-get autoremove --purge --yes && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/root/entrypoint.sh"]
