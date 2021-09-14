# Tests

TuxRun support some tests, each tests is supported on some but not all architectures.

!!! tip "Listing tests"
    You can list the supported tests with:
    ```shell
    tuxrun --list-tests
    ```

## FVP devices

Device              | Tests       | Parameters               |
--------------------|-------------|--------------------------|
fvp-morello-android | binder      | USERDATA                 |
fvp-morello-android | bionic      | USERDATA, GTEST_FILTER\* |
fvp-morello-android | compartment | USERDATA                 |
fvp-morello-android | device-tree |                          |
fvp-morello-android | dvfs        |                          |
fvp-morello-android | lldb        | LLDB_URL, TC_URL         |
fvp-morello-android | logd        | USERDATA                 |
fvp-morello-android | multicore   |                          |
fvp-morello-oe      | fwts        |                          |

!!! tip "Passing parameters"
    In order to pass parameters, use `tuxrun --parameters USERDATA=http://...`

!!! tip "Default parameters"
    **GTEST_FILTER** is optional and defaults to
    ```
    string_nofortify.*-string_nofortify.strlcat_overread:string_nofortify.bcopy:string_nofortify.memmove
    ```

## QEMU devices

Device  | Tests               |
--------|---------------------|
qemu-\* | command             |
qemu-\* | ltp-fcntl-locktests |
qemu-\* | ltp-fs_bind         |
qemu-\* | ltp-fs_perms_simple |
qemu-\* | ltp-fsx             |
qemu-\* | ltp-nptl            |
qemu-\* | ltp-smoke           |
