# Tests

TuxRun support some tests, each tests is supported on some but not all architectures.

!!! tip "Listing tests"
    You can list the supported tests with:
    ```shell
    tuxrun --list-tests
    ```

## FVP devices

Device              | Tests               |
--------------------|---------------------|
fvp-morello-android |binder               |
fvp-morello-android |bionic               |
fvp-morello-android |compartment          |
fvp-morello-android |device-tree          |
fvp-morello-android |dvfs                 |
fvp-morello-android |logd                 |
fvp-morello-android |multicore            |
fvp-morello-oe      |fwts                 |

## QEMU devices

Device              | Tests               |
--------------------|---------------------|
command             | qemu-\*             |
ltp-fcntl-locktests | qemu-\*             |
ltp-fs_bind         | qemu-\*             |
ltp-fs_perms_simple | qemu-\*             |
ltp-fsx             | qemu-\*             |
ltp-nptl            | qemu-\*             |
ltp-smoke           | qemu-\*             |
