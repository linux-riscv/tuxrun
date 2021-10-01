#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

import argparse
import contextlib
import json
import logging
from pathlib import Path
import shlex
import shutil
import signal
import sys
import tempfile
from urllib.parse import urlparse

from tuxrun import __version__
from tuxrun.assets import get_rootfs, get_test_definitions, ROOTFS
from tuxrun.devices import Device
from tuxrun.exceptions import InvalidArgument
from tuxrun.requests import requests_get
from tuxrun.runtimes import Runtime
import tuxrun.templates as templates
from tuxrun.tuxmake import TuxMakeBuild
from tuxrun.results import Results
from tuxrun.utils import TTYProgressIndicator
from tuxrun.writer import Writer
from tuxrun.yaml import yaml_load


###########
# GLobals #
###########
LOG = logging.getLogger("tuxrun")


###########
# Helpers #
###########
def download(src, dst):
    url = urlparse(src)
    if url.scheme in ["http", "https"]:
        ret = requests_get(src)
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

    path = Path(string if url.scheme == "" else url.path)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{path} no such file or directory")
    return f"file://{path.expanduser().resolve()}"


def pathnone(string):
    if string is None:
        return None

    path = Path(string)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{path} no such file or directory")
    return path.expanduser().resolve()


def tuxmake_directory(s):
    try:
        return TuxMakeBuild(s)
    except TuxMakeBuild.Invalid as e:
        raise argparse.ArgumentTypeError(str(e))


class ListDevicesAction(argparse.Action):
    def __init__(
        self, option_strings, help, dest=argparse.SUPPRESS, default=argparse.SUPPRESS
    ):
        super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser._print_message("\n".join(Device.list()) + "\n", sys.stderr)
        parser.exit()


class ListTestsAction(argparse.Action):
    def __init__(
        self, option_strings, help, dest=argparse.SUPPRESS, default=argparse.SUPPRESS
    ):
        super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser._print_message("\n".join(templates.tests_list()) + "\n", sys.stderr)
        parser.exit()


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        for value in values:
            key, value = value.split("=")
            getattr(namespace, self.dest)[key] = value


class UpdateCacheAction(argparse.Action):
    def __init__(
        self, option_strings, help, dest=argparse.SUPPRESS, default=argparse.SUPPRESS
    ):
        super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print("Updating local cache:")
        print("* Rootfs:")
        for device in [d for d in Device.list() if d in ROOTFS]:
            print(f"  * {device}")
            get_rootfs(
                device, progress=TTYProgressIndicator("Downloading root filesystem")
            )
        print("* Test definitions")
        get_test_definitions(
            progress=TTYProgressIndicator("Downloading test definitions")
        )
        parser.exit()


##########
# Setups #
##########
def filter_options(options):
    keys = [
        "device",
        "tuxmake",
        "device_dict",
        "definition",
        "runtime",
        "image",
        "log_file",
        "results",
        "debug",
    ]
    return {k: getattr(options, k) for k in vars(options) if k not in keys}


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
        choices=Device.list(),
    )

    group = parser.add_argument_group("listing")
    group.add_argument(
        "--list-devices", action=ListDevicesAction, help="List available devices"
    )
    group.add_argument(
        "--list-tests", action=ListTestsAction, help="List available tests"
    )

    group = parser.add_argument_group("cache")
    group.add_argument(
        "--update-cache", action=UpdateCacheAction, help="Update assets cache"
    )

    group = parser.add_argument_group("artefacts")

    def artefact(name):
        group.add_argument(
            f"--{name}",
            default=None,
            metavar="URL",
            type=pathurlnone,
            help=f"{name} URL",
        )

    artefact("bios")
    artefact("dtb")
    artefact("kernel")
    artefact("mcp-fw")
    artefact("mcp-romfw")
    artefact("modules")
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
    artefact("rootfs")
    artefact("scp-fw")
    artefact("scp-romfw")
    group.add_argument(
        "--tuxmake",
        metavar="DIRECTORY",
        default=None,
        type=tuxmake_directory,
        help="directory containing a TuxMake build",
    )
    artefact("uefi")

    group = parser.add_argument_group("test parameters")
    group.add_argument(
        "--parameters",
        metavar="K=V",
        default={},
        type=str,
        help="test parameters as key=value",
        action=KeyValueAction,
        nargs="+",
    )

    group = parser.add_argument_group("run options")
    group.add_argument(
        "--tests",
        nargs="+",
        default=[],
        metavar="T",
        help="test suites",
        choices=templates.tests_list(),
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
    group.add_argument(
        "--device-dict", default=None, type=pathnone, help="Device configuration"
    )
    group.add_argument(
        "--definition", default=None, type=pathnone, help="Job definition"
    )

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

    group = parser.add_argument_group("output")
    group.add_argument("--log-file", default=None, type=Path, help="Store logs to file")
    group.add_argument(
        "--results", default=None, type=Path, help="Save test results to file (JSON)"
    )

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

        device = Device.select(options.device)()
        definition = device.definition(
            bios=options.bios,
            command=command,
            device=options.device,
            dtb=options.dtb,
            kernel=options.kernel,
            mcp_fw=options.mcp_fw,
            mcp_romfw=options.mcp_romfw,
            overlays=overlays,
            rootfs=options.rootfs,
            rootfs_partition=options.partition,
            scp_fw=options.scp_fw,
            scp_romfw=options.scp_romfw,
            tests=options.tests,
            test_definitions=test_definitions,
            timeouts=templates.timeouts(),
            tmpdir=tmpdir,
            tux_boot_args=options.boot_args.replace('"', ""),
            uefi=options.uefi,
            parameters=options.parameters,
        )
        LOG.debug("job definition")
        LOG.debug(definition)

        context = yaml_load(definition).get("context", {})
        device_dict = device.device_dict(context)
        LOG.debug("device dictionary")
        LOG.debug(device_dict)

        (tmpdir / "definition.yaml").write_text(definition, encoding="utf-8")
        (tmpdir / "device.yaml").write_text(device_dict, encoding="utf-8")

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
    runtime = Runtime.select(options.runtime)()
    runtime.name(tmpdir.name)
    runtime.image(options.image)

    runtime.bind(tmpdir)
    for path in [
        options.bios,
        options.dtb,
        options.kernel,
        options.mcp_fw,
        options.mcp_romfw,
        options.rootfs,
        options.scp_fw,
        options.scp_romfw,
        options.uefi,
    ] + extra_assets:
        if not path:
            continue
        if urlparse(path).scheme == "file":
            runtime.bind(path[7:], ro=True)

    if options.device and options.device.startswith("fvp-") and runtime.container:
        runtime.bind(f"{tmpdir}/dispatcher")
        (tmpdir / "dispatcher").mkdir()
        dispatcher = templates.dispatchers.get_template(
            "dispatcher.yaml.jinja2"
        ).render(prefix=f"{tmpdir}/dispatcher/")
        LOG.debug("dispatcher config")
        LOG.debug(dispatcher)

        (tmpdir / "dispatcher.yaml").write_text(dispatcher, encoding="utf-8")
        # Add dispatcher.yaml to the command line arguments
        args.insert(-1, "--dispatcher")
        args.insert(-1, str(tmpdir / "dispatcher.yaml"))

    # Forward the signal to the runtime
    def handler(*_):
        runtime.kill()

    signal.signal(signal.SIGHUP, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGUSR1, handler)
    signal.signal(signal.SIGUSR2, handler)

    # start the pre_run command
    if options.device and options.device.startswith("fvp-"):
        LOG.debug("Pre run command")
        runtime.pre_run(tmpdir)

    results = Results()
    # Start the writer (stderr or log-file)
    with Writer(options.log_file) as writer:
        # Start the runtime
        with runtime.run(args):
            for line in runtime.lines():
                writer.write(line)
                results.parse(line)
    runtime.post_run()
    if options.results:
        options.results.write_text(json.dumps(results.data))
    return max([runtime.ret(), results.ret()])


def main() -> int:
    # Parse command line
    parser = setup_parser()
    options = parser.parse_args()

    # Setup logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(logging.DEBUG if options.debug else logging.INFO)

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
        parser.error(
            "tuxrun: error: artefacts or configuration files argument groups are required"
        )
    if first_group and second_group:
        parser.error(
            "tuxrun: error: artefacts and configuration files argument groups are mutualy exclusive"
        )

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
            parser.error("argument --device is required")

        if options.device.startswith("qemu-"):
            options.rootfs = pathurlnone(
                get_rootfs(
                    options.device,
                    options.rootfs,
                    TTYProgressIndicator("Downloading root filesystem"),
                )
            )

        if options.command:
            options.tests.append("command")

        try:
            Device.select(options.device)().validate(**filter_options(options))
        except InvalidArgument as exc:
            parser.error(str(exc))

    # --device-dict/--definition are mandatory
    else:
        if not options.device_dict:
            parser.error("tuxrun: error: argument --device-dict is required")
        if not options.definition:
            parser.error("tuxrun: error: argument --definition is required")

    # Create the temp directory
    tmpdir = Path(tempfile.mkdtemp(prefix="tuxrun-"))
    LOG.debug(f"temporary directory: '{tmpdir}'")
    try:
        return run(options, tmpdir)
    except Exception as exc:
        LOG.error("Raised an exception %s", exc)
        raise
    finally:
        with contextlib.suppress(FileNotFoundError, PermissionError):
            shutil.rmtree(tmpdir)


def start():
    if __name__ == "__main__":
        sys.exit(main())


start()
