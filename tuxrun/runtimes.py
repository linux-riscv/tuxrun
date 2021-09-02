# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

import contextlib
import logging
import os
from pathlib import Path
import subprocess


LOG = logging.getLogger("tuxrun")


class Runtime:
    binary = ""
    prefix = [""]

    def __init__(self):
        self.__bindings__ = []
        self.__image__ = None
        self.__name__ = None
        self.__pre_proc__ = None
        self.__proc__ = None
        self.__sub_procs__ = []
        self.__ret__ = None

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

    @contextlib.contextmanager
    def run(self, args):
        args = self.cmd(args)
        LOG.debug("Calling %s", " ".join(args))
        try:
            self.__proc__ = subprocess.Popen(
                args,
                bufsize=1,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setpgrp,
            )
            yield
        except FileNotFoundError as exc:
            LOG.error("File not found '%s'", exc.filename)
            raise
        except Exception as exc:
            LOG.exception(exc)
            if self.__proc__ is not None:
                self.kill()
                _, errs = self.__proc__.communicate()
                for err in [e for e in errs.split("\n") if e]:
                    LOG.error("err: %s", err)
            raise
        finally:
            self.__ret__ = self.__proc__.wait()
            for proc in self.__sub_procs__:
                proc.wait()

    def lines(self):
        return self.__proc__.stderr

    def kill(self):
        self.__proc__.kill()

    def ret(self):
        return self.__ret__


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

    def kill(self):
        args = [self.binary, "stop", "--time", "60", self.__name__]
        with contextlib.suppress(FileNotFoundError):
            proc = subprocess.Popen(
                args,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                preexec_fn=os.setpgrp,
            )
            self.__sub_procs__.append(proc)


class DockerRuntime(ContainerRuntime):
    binary = "docker"
    prefix = ["docker", "run", "--rm", "--hostname", "tuxrun"]


class PodmanRuntime(ContainerRuntime):
    binary = "podman"
    prefix = ["podman", "run", "--rm", "--quiet", "--hostname", "tuxrun"]


class NullRuntime(Runtime):
    def cmd(self, args):
        return args
