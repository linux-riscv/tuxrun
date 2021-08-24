# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path


class Runtime:
    prefix = [""]

    def __init__(self):
        self.__bindings__ = []
        self.__image__ = None
        self.__name__ = None
        self.__pre_proc__ = None

    @classmethod
    def select(cls, name):
        if name == "docker":
            return DockerRuntime
        if name == "podman":
            return PodmanRuntime
        return NullRuntime

    def bind(self, src, dst=None, ro=False):
        if dst is None:
            dst = src
        self.__bindings__.append((src, dst, ro))

    def image(self, image):
        self.__image__ = image

    def name(self, name):
        self.__name__ = name

    def cmd(self, args):
        raise NotImplementedError()


class ContainerRuntime(Runtime):
    def __init__(self):
        super().__init__()
        self.bind("/boot", ro=True)
        self.bind("/lib/modules", ro=True)
        # Bind /dev/kvm is available
        if Path("/dev/kvm").exists():
            self.bind("/dev/kvm")
        # Bind /var/tmp/.guestfs-$id if available
        guestfs = Path(f"/var/tmp/.guestfs-{os.getuid()}")
        if guestfs.exists():
            self.bind(guestfs, "/var/tmp/.guestfs-0")

    def cmd(self, args):
        prefix = self.prefix
        for binding in self.__bindings__:
            (src, dst, ro) = binding
            ro = "ro" if ro else "rw"
            prefix.extend(["-v", f"{src}:{dst}:{ro}"])
        prefix.extend(["--name", self.__name__])
        return prefix + [self.__image__] + args


class DockerRuntime(ContainerRuntime):
    prefix = ["docker", "run", "--rm", "--hostname", "tuxrun"]


class PodmanRuntime(ContainerRuntime):
    prefix = ["podman", "run", "--rm", "--quiet", "--hostname", "tuxrun"]


class NullRuntime(Runtime):
    def cmd(self, args):
        return args
