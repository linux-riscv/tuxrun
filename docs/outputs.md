# TuxRun outputs

TuxRun allows to record the outputs and results.

## Logs

By default, TuxRun will output the logs on the standard output. It's possible
to record the logs as `yaml` in a file with:

```shell
tuxrun --device qemu-armv5 --log-file logs.yaml
```

TuxRun can also extract the device output and save the logs as either `html` or `text`:

```shell
tuxrun --device qemu-armv5 --log-file-html logs.html --log-file-text logs.txt
```

## Results

When running the tests, TuxRun is recording the results of each individual
tests. The file can be dumped on the file system as `json`:

```shell
tuxrun --device qemu-armv5 --results results.json
```
