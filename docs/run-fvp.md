# Running under FVP

TuxRun allows to run linux kernel under FVP for Morello.

!!! note "Supported devices"
    See the [architecture matrix](devices.md#fvp-devices) for the supported devices.

## Preparing the environment

In order to use TuxRun with FVP, you have to build two containers:

* tuxrun fvp image
* morello fvp model

First close the git repository:

```shell
git clone https://gitlab.com/Linaro/tuxrun
cd tuxrun
```

### TuxRun fvp image

Build the TuxRun image

```shell
cd share/fvp
podman build --tag tuxrun:fvp .
```

!!! tip "Runtime"
    The default runtime is podman but you can also use docker if you prefer. In
    this case, build using docker.

### Morello fvp model

Build the container containing the Morello FVP model:

```shell
cd share/fvp/morello
podman build --tag fvp:morello-0.11.19 .
```

!!! warning "Container tag"
    The container should be named **fvp:morello-0.11.19** in order for TuxRun
    to work.

## Boot testing

In order to run a simple boot test on **fvp-morello-busybox**:

```shell
tuxrun --image tuxrun:fvp \
       --device fvp-morello-buxybox \
       --mcp-fw https://example.com/fvp/morello/mcp_fw.bin \
       --mcp-romfw https://example.com/fvp/morello/mcp_romfw.bin \
       --rootfs https://example.com/fvp/morello/rootfs.img.xz \
       --scp-fw https://example.com/fvp/morello/scp_fw.bin \
       --scp-romfw https://example.com/fvp/morello/scp_romfw.bin \
       --uefi https://example.com/fvp/morello/uefi.bin
```

## Testing on Android

In order to run an Android test on **fvp-morello-android**:

```shell
tuxrun --image tuxrun:fvp \
       --device fvp-morello-android \
       --mcp-fw https://example.com/fvp/morello/mcp_fw.bin \
       --mcp-romfw https://example.com/fvp/morello/mcp_romfw.bin \
       --rootfs https://example.com/fvp/morello/rootfs.img.xz \
       --scp-fw https://example.com/fvp/morello/scp_fw.bin \
       --scp-romfw https://example.com/fvp/morello/scp_romfw.bin \
       --uefi https://example.com/fvp/morello/uefi.bin \
       --userdata https://example.com/fvp/morello/userdata.tar.xz \
       --tests binder
```

!!! tip "Android boot test"
    When running an Android boot test, **--userdata** is not needed (and won't
    be used).
