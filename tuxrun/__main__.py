#!/usr/bin/python3
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

import jinja2
import requests
import yaml

from tuxrun.yaml import yaml_load


#############
# Constants #
#############
BASE = (Path(__file__) / ".." / "..").resolve()

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

DEVICES = [
    "qemu-arm",
    "qemu-arm64",
    "qemu-i386",
    "qemu-mips64",
    "qemu-ppc64",
    "qemu-riscv64",
    "qemu-x86_64",
]


###########
# Helpers #
###########
def download(src, dst):
    url = urlparse(src)
    if url.scheme in ["http", "https"]:
        ret = requests.get(src)
        dst.write_text(ret.text, encoding="utf-8")
    else:
        shutil.copyfile(src, dst)


##########
# Setups #
##########
def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tuxrun", description="TuxRun")

    group = parser.add_argument_group("Configuration")
    group.add_argument("--device", default=None, help="Device type", choices=DEVICES)
    group.add_argument("--kernel", default=None, help="kernel URL")
    group.add_argument("--modules", default=None, help="modules URL")
    group.add_argument("--tests", default="", help="modules URL", choices=["ltp-smoke"])

    group = parser.add_argument_group("configuration files")
    group.add_argument("--device-dict", default=None, help="Device configuration")
    group.add_argument("--definition", default=None, help="Job definition")

    group = parser.add_argument_group("runtime")
    group.add_argument(
        "--runtime", default="podman", choices=["local", "podman"], help="Runtime"
    )

    parser.add_argument(
        "--log-file", default=None, type=Path, help="Store logs to file"
    )

    return parser


##############
# Entrypoint #
##############
def _main(options, tmpdir: Path) -> int:
    # Render the job definition and device dictionary
    if options.device:
        def_env = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(
                str(BASE / "share" / "templates" / "definition")
            ),
        )
        dev_env = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(
                str(BASE / "share" / "templates" / "device")
            ),
        )

        definition = def_env.get_template(f"{options.device}.yaml.jinja2").render(
            device=options.device,
            kernel=options.kernel,
            modules=options.modules,
            tests=[t for t in options.tests.split(",") if t],
        )
        context = yaml_load(definition).get("context", {})
        device = dev_env.get_template("qemu.jinja2").render(**context)
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

    # Use podman if requested
    if options.runtime == "podman":
        args = [
            "podman",
            "run",
            "--quiet",
            "--rm",
            "-v",
            f"{tmpdir}:{tmpdir}",
            "-v",
            "/boot:/boot:ro",
            "-v",
            "/lib/modules:/lib/modules:ro",
            "--hostname",
            "tuxrun",
            "tuxrun:latest",
        ] + args

    # Should we write lava-run logs to a file
    log_file = None
    if options.log_file is not None:
        log_file = options.log_file.open("w")

    try:
        proc = subprocess.Popen(args, bufsize=1, stderr=subprocess.PIPE, text=True)
        assert proc.stderr is not None
        for line in proc.stderr:
            line = line.rstrip("\n")
            try:
                data = yaml.load(line, Loader=yaml.CFullLoader)  # type: ignore
                if not data:
                    continue
                if log_file is not None:
                    log_file.write("- " + line + "\n")
                else:
                    level = data["lvl"]
                    msg = data["msg"]
                    timestamp = data["dt"].split(".")[0]

                    sys.stdout.write(
                        f"{COLORS['dt']}{timestamp}{COLORS['end']} {COLORS[level]}{msg}{COLORS['end']}\n"
                    )
            except (yaml.YAMLError, KeyError):
                sys.stdout.write(line + "\n")
            sys.stdout.flush()
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

    # --device/--kernel/--modules/--tests and --device-dict/--definition are
    # mutualy exclusive and required
    first_group = bool(
        options.device or options.kernel or options.modules or options.tests
    )
    second_group = bool(options.device_dict or options.definition)
    if not first_group and not second_group:
        parser.print_usage()
        sys.stderr.write(
            "tuxrun: error: configuration or configuration files argument groups are required\n"
        )
        return 1
    if first_group and second_group:
        parser.print_usage()
        sys.stderr.write(
            "tuxrun: error: configuration and configuration files argument groups are mutualy exclusive\n"
        )
        return 1

    # --device/--kernel are mandatory
    if first_group:
        if not options.device:
            parser.print_usage()
            sys.stderr.write("tuxrun: error: argument --device is required\n")
            return 1
        if not options.kernel:
            parser.print_usage()
            sys.stderr.write("tuxrun: error: argument --kernel is required\n")
            return 1
    # --device-dict/--definition are mandatory
    else:
        if not options.device_dict:
            parser.print_usage()
            sys.stderr.write("tuxrun: error: argument --device-dict is required\n")
            return 1
        if not options.definition:
            parser.print_usage()
            sys.stderr.write("tuxrun: error: argument --definition is required\n")
            return 1

    # Create the temp directory
    tmpdir = Path(tempfile.mkdtemp(prefix="tuxrun-"))
    try:
        return _main(options, tmpdir)
    finally:
        shutil.rmtree(tmpdir)


def start():
    if __name__ == "__main__":
        sys.exit(main())


start()
