# vim: set ts=4
#
# Copyright 2025, Rivos Inc.
#
# SPDX-License-Identifier: MIT

from tuxrun.tests import Test


class Cfi(Test):
    devices = ["qemu-*", "fvp-aemva", "avh-imx93", "avh-rpi4b"]
    name = "cfi"
    timeout = 45
    need_test_definition = True

    def render(self, **kwargs):
        kwargs["name"] = self.name
        kwargs["timeout"] = self.timeout

        return self._render("cfi.yaml.jinja2", **kwargs)
