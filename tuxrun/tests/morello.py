# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

from typing import List, Optional

from tuxrun.exceptions import InvalidArgument
from tuxrun.tests import Test


class MorelloTest(Test):
    template = "morello.yaml.jinja2"
    test_def_name: Optional[str] = None
    required_parameters: List[str] = []

    def validate(self, device, parameters, **kwargs):
        super().validate(device=device, parameters=parameters, **kwargs)
        missing = set(self.parameters) - set(parameters.keys())
        if missing:
            raise InvalidArgument(f"Missing --parameters {', '.join(missing)}")
        invalid = set(parameters.keys()) - set(self.parameters)
        if invalid:
            raise InvalidArgument(f"Invalid --parameters {', '.join(invalid)}")

    def render(self, **kwargs):
        kwargs["name"] = self.name
        kwargs["timeout"] = self.timeout
        kwargs["test_def_name"] = (
            self.test_def_name if self.test_def_name else self.name
        )

        # remap some parameters
        MAPPINGS = {"LLDB_URL": "LLDB_TESTS_URL", "USERDATA": "USERDATA_URL"}
        for key, value in MAPPINGS.items():
            if key in kwargs["parameters"]:
                kwargs["parameters"][value] = kwargs["parameters"].pop(key)

        return self._render(self.template, **kwargs)


class MorelloAndroidTest(MorelloTest):
    device = "fvp-morello-android"


class MorelloBinder(MorelloAndroidTest):
    name = "binder"
    timeout = 34
    parameters = ["USERDATA"]


class MorelloBionic(MorelloAndroidTest):
    name = "bionic"
    timeout = 1000
    parameters = ["USERDATA"]

    def render(self, parameters, **kwargs):
        parameters["TEST_PATHS"] = "nativetest64 nativetestc64"
        parameters["TEST_TYPE"] = parameters.get(
            "BIONIC_TEST_TYPE",
            "static",
        )
        parameters["GTEST_FILTER"] = parameters.get(
            "GTEST_FILTER",
            "string_nofortify.*-string_nofortify.strlcat_overread:string_nofortify.bcopy:string_nofortify.memmove",
        )

        return super().render(parameters=parameters, **kwargs)


class MorelloBoringSSL(MorelloAndroidTest):
    name = "boringssl"
    timeout = 240
    parameters = ["SYSTEM_URL"]


class MorelloCompartment(MorelloAndroidTest):
    name = "compartment"
    timeout = 15
    parameters = ["USERDATA"]
    test_def_name = "compartment-demo"


class MorelloDeviceTree(MorelloAndroidTest):
    name = "device-tree"
    timeout = 15


class MorelloDvfs(MorelloAndroidTest):
    name = "dvfs"
    timeout = 15


class MorelloFWTS(MorelloTest):
    name = "fwts"
    timeout = 120
    device = "fvp-morello-oe"
    template = "fwts.yaml.jinja2"


class MorelloLibJPEGTurbo(MorelloAndroidTest):
    name = "libjpeg-turbo"
    timeout = 30
    parameters = ["LIBJPEG_TURBO_URL", "SYSTEM_URL"]


class MorelloLibPNG(MorelloAndroidTest):
    name = "libpng"
    timeout = 30
    parameters = ["PNG_URL", "SYSTEM_URL"]


class MorelloLibPDFium(MorelloAndroidTest):
    name = "libpdfium"
    timeout = 30
    parameters = ["PDFIUM_URL", "SYSTEM_URL"]


class MorelloLLDB(MorelloAndroidTest):
    name = "lldb"
    timeout = 30
    parameters = ["LLDB_URL", "TC_URL"]


class MorelloLOGD(MorelloAndroidTest):
    name = "logd"
    timeout = 420
    parameters = ["USERDATA"]


class MorelloMulticore(MorelloAndroidTest):
    name = "multicore"
    timeout = 15
    test_def_name = "multicore-boot"


class Morellozlib(MorelloAndroidTest):
    name = "zlib"
    timeout = 30
    parameters = ["SYSTEM_URL"]
