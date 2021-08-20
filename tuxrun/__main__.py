#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

import argparse
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

import requests
import yaml

from tuxrun import __version__
from tuxrun.assets import KERNELS, get_rootfs, get_test_definitions
import tuxrun.templates as templates
from tuxrun.tuxmake import TuxMakeBuild
from tuxrun.utils import TTYProgressIndicator
from tuxrun.yaml import yaml_load


#############
# Constants #
#############
COLORS = {
    "exception": "\033[1;31m",
    "error": "\033[1;31m",
    "warning": "\033[1;33m",
    "info": "\033[1;37m",
    "debug": "\033[0;37m",
    "target": "\033[32m",
    "input": "\033[0;35m",
    "feedback": "\033[0;33m",
    "results": "\033[1;34m",
    "dt": "\033[0;90m",
    "end": "\033[0m",
}


###########
# Helpers #
###########
def debug(options, msg):
    if options.debug:
        for line in msg.split("\n"):
            print(f"tuxrun: {line}")


def download(src, dst):
    url = urlparse(src)
    if url.scheme in ["http", "https"]:
        ret = requests.get(src)
        dst.write_text(ret.text, encoding="utf-8")
    else:
        shutil.copyfile(src, dst)


def pathurlnone(string):
    if string is None:
        return None
    url = urlparse(string)
    if url.scheme in ["http", "https"]:
        return string
    if url.scheme not in ["", "file"]:
        raise argparse.ArgumentTypeError(f"Invalid scheme '{url.scheme}'")

    path = string if url.scheme == "" else url.path
    return f"file://{Path(path).expanduser().resolve()}"


def tuxmake_directory(s):
    try:
        return TuxMakeBuild(s)
    except TuxMakeBuild.Invalid as e:
        raise argparse.ArgumentTypeError(str(e))


##########
# Setups #
##########
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tuxrun", description="TuxRun")

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s, {__version__}"
    )
    parser.add_argument(
        "--device",
        default=None,
        metavar="NAME",
        help="Device type",
        choices=templates.devices_list(),
    )

    group = parser.add_argument_group("artefacts")
    group.add_argument(
        "--bios", default=None, metavar="URL", type=pathurlnone, help="bios URL"
    )
    group.add_argument(
        "--dtb", default=None, metavar="URL", type=pathurlnone, help="dtb URL"
    )
    group.add_argument(
        "--kernel", default=None, metavar="URL", type=pathurlnone, help="kernel URL"
    )
    group.add_argument(
        "--modules", default=None, metavar="URL", type=pathurlnone, help="modules URL"
    )
    group.add_argument(
        "--overlay",
        default=[],
        metavar="URL",
        type=pathurlnone,
        help="Tarball with overlay for rootfs. Can be specified multiple times",
        action="append",
        dest="overlays",
    )
    group.add_argument(
        "--partition",
        default=None,
        metavar="NUMBER",
        type=int,
        help="rootfs partition number",
    )
    group.add_argument(
        "--rootfs", default=None, metavar="URL", type=pathurlnone, help="rootfs URL"
    )
    group.add_argument(
        "--tuxmake",
        metavar="DIRECTORY",
        default=None,
        type=tuxmake_directory,
        help="directory containing a TuxMake build",
    )

    group = parser.add_argument_group("run options")
    group.add_argument(
        "--tests",
        nargs="+",
        default=[],
        metavar="T",
        help="test suites",
        choices=templates.tests(),
    )
    group.add_argument(
        "--boot-args", default="", metavar="ARGS", help="extend boot arguments"
    )
    group.add_argument(
        "command",
        nargs="*",
        help="Command to run inside the VM",
    )

    group = parser.add_argument_group("configuration files")
    group.add_argument("--device-dict", default=None, help="Device configuration")
    group.add_argument("--definition", default=None, help="Job definition")

    group = parser.add_argument_group("runtime")
    group.add_argument(
        "--runtime",
        default="podman",
        metavar="RUNTIME",
        choices=["docker", "null", "podman"],
        help="Runtime",
    )
    group.add_argument(
        "--image",
        default="docker.io/lavasoftware/lava-dispatcher:latest",
        help="Image to use",
    )

    group = parser.add_argument_group("logging")
    group.add_argument("--log-file", default=None, type=Path, help="Store logs to file")

    group = parser.add_argument_group("debugging")
    group.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Print more debug information about tuxrun",
    )

    return parser


##############
# Entrypoint #
##############
def run(options, tmpdir: Path) -> int:
    # Render the job definition and device dictionary
    extra_assets = []
    if options.device:
        kernel_compression = None
        if options.kernel.endswith(".gz"):
            kernel_compression = "gz"
        if options.kernel.endswith(".xz"):
            kernel_compression = "xz"

        overlays = []
        if options.modules:
            overlays.append(("modules", options.modules))
            extra_assets.append(options.modules)
        for item in options.overlays:
            name = str(hash(item)).replace("-", "n")
            overlays.append((name, item))
            extra_assets.append(item)

        test_definitions = "file://" + get_test_definitions(
            TTYProgressIndicator("Downloading test definitions")
        )
        extra_assets.append(test_definitions)

        command = " ".join([shlex.quote(s) for s in options.command])

        definition = templates.jobs.get_template(
            f"{options.device}.yaml.jinja2"
        ).render(
            device=options.device,
            kernel=options.kernel,
            overlays=overlays,
            bios=options.bios,
            dtb=options.dtb,
            rootfs=options.rootfs,
            rootfs_partition=options.partition,
            tests=options.tests,
            command=command,
            test_definitions=test_definitions,
            timeouts=templates.timeouts(),
            tux_boot_args=options.boot_args.replace('"', ""),
            kernel_compression=kernel_compression,
        )
        debug(options, "job definition")
        debug(options, definition)

        context = yaml_load(definition).get("context", {})
        device = templates.devices.get_template("qemu.jinja2").render(**context)
        debug(options, "device dictionary")
        debug(options, device)

        (tmpdir / "definition.yaml").write_text(definition, encoding="utf-8")
        (tmpdir / "device.yaml").write_text(device, encoding="utf-8")

    # Use the provided ones
    else:
        # Download if needed and copy to tmpdir
        download(str(options.device_dict), (tmpdir / "device.yaml"))
        download(str(options.definition), (tmpdir / "definition.yaml"))

    args = [
        "lava-run",
        "--device",
        str(tmpdir / "device.yaml"),
        "--job-id",
        "1",
        "--output-dir",
        "output",
        str(tmpdir / "definition.yaml"),
    ]

    # Use a container runtime
    if options.runtime in ["docker", "podman"]:
        bindings = [
            f"{tmpdir}:{tmpdir}",
            "/boot:/boot:ro",
            "/lib/modules:/lib/modules:ro",
        ]
        for path in [
            options.bios,
            options.dtb,
            options.kernel,
            options.rootfs,
        ] + extra_assets:
            if not path:
                continue
            if urlparse(path).scheme == "file":
                bindings.append(f"{path[7:]}:{path[7:]}:ro")

        # Bind /dev/kvm is available
        if Path("/dev/kvm").exists():
            bindings.append("/dev/kvm:/dev/kvm:rw")
        # Bind /var/tmp/.guestfs-$id if available
        guestfs = Path(f"/var/tmp/.guestfs-{os.getuid()}")
        if guestfs.exists():
            bindings.append(f"{guestfs}:/var/tmp/.guestfs-0:rw")

        if options.runtime == "docker":
            runtime_args = ["docker", "run"]
        elif options.runtime == "podman":
            runtime_args = ["podman", "run", "--quiet"]

        args = (
            runtime_args
            + ["--rm", "--hostname", "tuxrun"]
            + [path for binding in bindings for path in ["-v", binding]]
            + [options.image]
            + args
        )

    # Should we write lava-run logs to a file
    log_file = None
    if options.log_file is not None:
        log_file = options.log_file.open("w")

    try:
        debug(options, f"Calling {' '.join(args)}")

        # Ignore the signal, this is handled by the runtim
        signal.signal(signal.SIGINT, lambda s, f: None)
        signal.signal(signal.SIGINT, lambda s, f: None)
        signal.signal(signal.SIGQUIT, lambda s, f: None)
        signal.signal(signal.SIGTERM, lambda s, f: None)
        signal.signal(signal.SIGUSR1, lambda s, f: None)
        signal.signal(signal.SIGUSR2, lambda s, f: None)

        # Start the subprocess
        proc = subprocess.Popen(args, bufsize=1, stderr=subprocess.PIPE, text=True)
        assert proc.stderr is not None
        for line in proc.stderr:
            line = line.rstrip("\n")
            try:
                data = yaml_load(line)
                if not data or not isinstance(data, dict):
                    debug(options, line)
                    continue
                if not set(["dt", "lvl", "msg"]).issubset(data.keys()):
                    debug(options, line)
                    continue

                if log_file is not None:
                    log_file.write("- " + line + "\n")
                else:
                    level = data["lvl"]
                    msg = data["msg"]
                    ns = " "
                    if level == "feedback" and "ns" in data:
                        ns = f" <{COLORS['feedback']}{data['ns']}{COLORS['end']}> "
                    timestamp = data["dt"].split(".")[0]

                    sys.stdout.write(
                        f"{COLORS['dt']}{timestamp}{COLORS['end']}{ns}{COLORS[level]}{msg}{COLORS['end']}\n"
                    )
            except yaml.YAMLError:
                debug(options, line)
        return proc.wait()
    except FileNotFoundError as exc:
        sys.stderr.write(f"File not found '{exc.filename}'\n")
        return 1
    except Exception:
        proc.kill()
        outs, errs = proc.communicate()
        # TODO: do something with outs and errs
        raise
    return 0


def main() -> int:
    # Parse command line
    parser = setup_parser()
    options = parser.parse_args()

    # --tuxmake/--device/--kernel/--modules/--tests and
    # --device-dict/--definition are mutualy exclusive and required
    first_group = bool(
        options.device
        or options.bios
        or options.dtb
        or options.kernel
        or options.modules
        or options.overlays
        or options.partition
        or options.rootfs
        or options.tuxmake
        or options.tests
        or options.boot_args
        or options.command
    )
    second_group = bool(options.device_dict or options.definition)
    if not first_group and not second_group:
        parser.print_usage(file=sys.stderr)
        sys.stderr.write(
            "tuxrun: error: artefacts or configuration files argument groups are required\n"
        )
        return 1
    if first_group and second_group:
        parser.print_usage(file=sys.stderr)
        sys.stderr.write(
            "tuxrun: error: artefacts and configuration files argument groups are mutualy exclusive\n"
        )
        return 1

    if first_group:
        if options.tuxmake:
            tuxmake = options.tuxmake
            if not options.kernel:
                options.kernel = f"file://{tuxmake.kernel}"
            if not options.modules and tuxmake.modules:
                options.modules = f"file://{tuxmake.modules}"
            if not options.device:
                options.device = f"qemu-{tuxmake.target_arch}"

        if not options.device:
            parser.print_usage(file=sys.stderr)
            sys.stderr.write("tuxrun: error: argument --device is required\n")
            return 1

        if not options.kernel:
            options.kernel = KERNELS[options.device]

        options.rootfs = pathurlnone(
            get_rootfs(
                options.device,
                options.rootfs,
                TTYProgressIndicator("Downloading root filesystem"),
            )
        )

        if options.command:
            options.tests.append("command")

        if options.bios and options.device != "qemu-riscv64":
            parser.print_usage(file=sys.stderr)
            sys.stderr.write(
                "tuxrun: error: argument --bios is only valid for qemu-riscv64 device\n"
            )
            return 1

        if options.dtb and options.device != "qemu-armv5":
            parser.print_usage(file=sys.stderr)
            sys.stderr.write(
                "tuxrun: error: argument --dtb is only valid for qemu-armv5 device\n"
            )
            return 1
    # --device-dict/--definition are mandatory
    else:
        if not options.device_dict:
            parser.print_usage(file=sys.stderr)
            sys.stderr.write("tuxrun: error: argument --device-dict is required\n")
            return 1
        if not options.definition:
            parser.print_usage(file=sys.stderr)
            sys.stderr.write("tuxrun: error: argument --definition is required\n")
            return 1

    # Create the temp directory
    tmpdir = Path(tempfile.mkdtemp(prefix="tuxrun-"))
    debug(options, f"temporary directory: '{tmpdir}'")
    try:
        return run(options, tmpdir)
    finally:
        shutil.rmtree(tmpdir)


def start():
    if __name__ == "__main__":
        sys.exit(main())


start()
