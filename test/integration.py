#!/usr/bin/python3
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml

from typing import Dict


#############
# Constants #
#############
KERNELS = {
    "qemu-armv5": "https://storage.tuxboot.com/armv5/zImage",
    "qemu-armv7": "https://storage.tuxboot.com/armv7/zImage",
    "qemu-arm64": "https://storage.tuxboot.com/arm64/Image",
    "qemu-i386": "https://storage.tuxboot.com/i386/bzImage",
    "qemu-mips64": "https://storage.tuxboot.com/mips64/vmlinux",
    "qemu-mips64el": "https://storage.tuxboot.com/mips64el/vmlinux",
    "qemu-ppc64": "https://storage.tuxboot.com/ppc64/vmlinux",
    "qemu-ppc64le": "https://storage.tuxboot.com/ppc64le/vmlinux",
    "qemu-riscv64": "https://storage.tuxboot.com/riscv64/Image",
    "qemu-sparc64": "https://storage.tuxboot.com/sparc64/vmlinux",
    "qemu-x86_64": "https://storage.tuxboot.com/x86_64/bzImage",
}


###########
# Helpers #
###########
def get_results(tmpdir: Path) -> Dict:
    required_keys = set(["msg", "lvl", "dt"])
    res = {}
    data = yaml.load(
        (tmpdir / "logs.yaml").read_text(encoding="utf-8"), Loader=yaml.CFullLoader
    )

    if data is None:
        return {}

    for line in data:
        if not isinstance(line, dict):
            continue
        if not required_keys.issubset(set(line.keys())):
            continue
        if line["lvl"] != "results":
            continue
        definition = line["msg"]["definition"]
        case = line["msg"]["case"]
        del line["msg"]["definition"]
        del line["msg"]["case"]
        res.setdefault(definition, {})[case] = line["msg"]

    return res


def get_simple_results(res: Dict) -> Dict:
    results = {
        "boot": res.get("lava", {}).get("login-action", {}).get("result", "fail")
    }
    for name in res:
        if name == "lava":
            continue
        key = "_".join(name.split("_")[1:])
        if all([res[name][case]["result"] in ["skip", "pass"] for case in res[name]]):
            results[key] = "pass"
        else:
            results[key] = "fail"
    return results


def get_job_result(results: Dict, simple_results: Dict) -> str:
    # lava.job is missing: error
    lava = results.get("lava", {}).get("job")
    if lava is None:
        return "error"

    if lava["result"] == "fail":
        if lava.get("error_type") == "Job":
            return "fail"
        return "error"

    if all([v == "pass" for (k, v) in simple_results.items()]):
        return "pass"
    return "fail"


def run(device, test, debug):
    tmpdir = Path(tempfile.mkdtemp(prefix="tuxrun-"))

    args = [
        "python3",
        "-m",
        "tuxrun",
        "--device",
        device,
        "--kernel",
        KERNELS[device],
        "--log-file",
        str(tmpdir / "logs.yaml"),
    ]
    if test:
        args.extend(["--tests", test])

    try:
        ret = subprocess.call(args)
        if ret != 0:
            print(f"Command return non-zero exist status {ret}")
            print((tmpdir / "logs.yaml").read_text(encoding="utf-8"))
            return ret

        results = get_results(tmpdir)
        simple_results = get_simple_results(results)
        result = get_job_result(results, simple_results)

        if debug:
            print("Results:")
            for res in results:
                print(f"* {res}: {results[res]}")

            print("\nSimple results:")
            for res in simple_results:
                print(f"* {res}: {simple_results[res]}")
            print(f"Result {result}")
        else:
            print(f"{result}")
        assert result == "pass"
    finally:
        shutil.rmtree(tmpdir)


##############
# Entrypoint #
##############
def main():
    parser = argparse.ArgumentParser(description="Integration tests")
    parser.add_argument(
        "--devices", default=list(KERNELS.keys()), nargs="+", help="devices"
    )
    parser.add_argument(
        "--tests", default=["boot", "ltp-smoke"], nargs="+", help="tests"
    )
    parser.add_argument("--debug", default=False, action="store_true", help="debug")
    options = parser.parse_args()

    for device in options.devices:
        for test in options.tests:
            print(f"=> {device} x {test}")
            run(device, "" if test == "boot" else test, options.debug)
            print("")


if __name__ == "__main__":
    sys.exit(main())
