import os
from pathlib import Path

import pytest

from tuxrun.devices import Device
from tuxrun.devices.qemu import QemuArmv5
from tuxrun.devices.fvp import FVPMorelloAndroid
import tuxrun.templates as templates


BASE = (Path(__file__) / "..").resolve()


def test_select():
    assert Device.select("qemu-armv5") == QemuArmv5
    assert Device.select("fvp-morello-android") == FVPMorelloAndroid

    with pytest.raises(NotImplementedError):
        Device.select("Hello")


@pytest.mark.parametrize(
    "device,args,filename",
    [
        (
            "qemu-arm64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-arm64.yaml",
        ),
        (
            "qemu-arm64",
            {
                "tests": ["ltp-smoke"],
                "tux_boot_args": "",
                "overlays": [],
                "test_definitions": "testdef.tar.zst",
            },
            "qemu-arm64-ltp-smoke.yaml",
        ),
        (
            "qemu-armv5",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-armv5.yaml",
        ),
        (
            "qemu-armv5",
            {
                "tests": ["ltp-nptl"],
                "tux_boot_args": "",
                "overlays": [],
                "test_definitions": "testdef.tar.zst",
            },
            "qemu-armv5-ltp-nptl.yaml",
        ),
        (
            "qemu-armv7",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-armv7.yaml",
        ),
        (
            "qemu-armv7",
            {"tests": [], "tux_boot_args": "", "overlays": [], "kernel": "zImage.xz"},
            "qemu-armv7-kernel-xz.yaml",
        ),
        (
            "qemu-i386",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-i386.yaml",
        ),
        (
            "qemu-i386",
            {"tests": [], "tux_boot_args": "", "overlays": [], "kernel": "bzImage.gz"},
            "qemu-i386-kernel-gz.yaml",
        ),
        (
            "qemu-mips32",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-mips32.yaml",
        ),
        (
            "qemu-mips32el",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-mips32el.yaml",
        ),
        (
            "qemu-mips64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-mips64.yaml",
        ),
        (
            "qemu-mips64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-mips64el.yaml",
        ),
        (
            "qemu-ppc32",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-ppc32.yaml",
        ),
        (
            "qemu-ppc64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-ppc64.yaml",
        ),
        (
            "qemu-ppc64le",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-ppc64le.yaml",
        ),
        (
            "qemu-riscv64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-riscv64.yaml",
        ),
        (
            "qemu-sparc64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-sparc64.yaml",
        ),
        (
            "qemu-x86_64",
            {"tests": [], "tux_boot_args": "", "overlays": []},
            "qemu-x86_64.yaml",
        ),
        (
            "fvp-morello-android",
            {
                "tests": [],
                "mcp_fw": "mcp_fw.bin",
                "mcp_romfw": "mcp_romfw.bin",
                "rootfs": "android-nano.img.xz",
                "scp_fw": "scp_fw.bin",
                "scp_romfw": "scp_romfw.bin",
                "uefi": "uefi.bin",
            },
            "fvp-morello-android.yaml",
        ),
        (
            "fvp-morello-busybox",
            {
                "tests": [],
                "mcp_fw": "mcp_fw.bin",
                "mcp_romfw": "mcp_romfw.bin",
                "rootfs": "busybox.img.xz",
                "scp_fw": "scp_fw.bin",
                "scp_romfw": "scp_romfw.bin",
                "uefi": "uefi.bin",
            },
            "fvp-morello-busybox.yaml",
        ),
        (
            "fvp-morello-oe",
            {
                "tests": [],
                "mcp_fw": "mcp_fw.bin",
                "mcp_romfw": "mcp_romfw.bin",
                "rootfs": "core-image-minimal-morello-fvp.wic",
                "scp_fw": "scp_fw.bin",
                "scp_romfw": "scp_romfw.bin",
                "uefi": "uefi.bin",
            },
            "fvp-morello-oe.yaml",
        ),
        (
            "fvp-morello-ubuntu",
            {
                "tests": [],
                "mcp_fw": "mcp_fw.bin",
                "mcp_romfw": "mcp_romfw.bin",
                "scp_fw": "scp_fw.bin",
                "scp_romfw": "scp_romfw.bin",
                "uefi": "uefi.bin",
            },
            "fvp-morello-ubuntu.yaml",
        ),
    ],
)
def test_definition(device, args, filename):
    if os.environ.get("TUXRUN_RENDER"):
        (BASE / "refs" / "definitions" / filename).write_text(
            Device.select(device)().definition(
                device=device,
                timeouts=templates.timeouts(),
                tmpdir=Path("/tmp/tuxrun-ci"),
                **args
            )
        )
    assert Device.select(device)().definition(
        device=device,
        timeouts=templates.timeouts(),
        tmpdir=Path("/tmp/tuxrun-ci"),
        **args
    ) == (BASE / "refs" / "definitions" / filename).read_text(encoding="utf-8")
