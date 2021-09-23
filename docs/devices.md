# Devices

TuxRun supports many architectures for both FVP and QEMU.

!!! tip "Listing devices"
    You can list the supported devices with:
    ```shell
    tuxrun --list-devices
    ```

## FVP devices

Device              | FVP version     |OS       |
--------------------|-----------------|---------|
fvp-morello-android | Morello 0.11.19 | Android |
fvp-morello-busybox | Morello 0.11.19 | Busybox |
fvp-morello-oe      | Morello 0.11.19 | OE      |

## QEMU devices

Device        | Description         | Machine     | CPU              | Kernel
--------------|---------------------|-------------|------------------|--------
qemu-arm64    | 64-bit ARMv8        | virt        | Cortex-A57       | Image
qemu-armv5    | 32-bit ARM          | versatilepb | arm926           | zImage
qemu-armv7    | 32-bit ARM          | virt        | Cortex-A15       | zImage
qemu-i386     | 32-bit X86          | q35         | coreduo          | bzImage
qemu-mips32   | 32-bit MIPS         | malta       | mips32r6-generic | vmlinux
qemu-mips32el | 32-bit MIPS (EL)    | malta       | mips32r6-generic | vmlinux
qemu-mips64   | 64-bit MIPS         | malta       | 24Kf             | vmlinux
qemu-mips64el | 64-bit MIPS (EL)    | malta       | 24Kf             | vmlinux
qemu-ppc32    | 32-bit PowerPC      | ppce500     | e500mc           | uImage
qemu-ppc64    | 64-bit PowerPC      | pSeries     | Power8           | vmlinux
qemu-ppc64le  | 64-bit PowerPC (EL) | pSeries     | Power8           | vmlinux
qemu-riscv64  | 64-bit RISC-V       | virt        | rv64             | Image
qemu-sparc64  | 64-bit Sparc        | sun4u       | UltraSPARC II    | vmlinux
qemu-x86_64   | 64-bit X86          | q35         | Nehalem          | bzImage
