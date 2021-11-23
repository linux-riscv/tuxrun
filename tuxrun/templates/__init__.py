# -*- coding: utf-8 -*-
# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

from functools import cache
from pathlib import Path

import jinja2


BASE = (Path(__file__) / "..").resolve()


@cache
def jobs():
    return jinja2.Environment(
        autoescape=False,
        trim_blocks=True,
        loader=jinja2.FileSystemLoader(str(BASE / "jobs")),
        undefined=jinja2.StrictUndefined,
    )


@cache
def devices():
    return jinja2.Environment(
        autoescape=False,
        trim_blocks=True,
        loader=jinja2.FileSystemLoader(str(BASE / "devices")),
    )


@cache
def dispatchers():
    return jinja2.Environment(
        autoescape=False,
        trim_blocks=True,
        loader=jinja2.FileSystemLoader(str(BASE / "dispatchers")),
    )


@cache
def wrappers():
    return jinja2.Environment(
        autoescape=False,
        trim_blocks=True,
        loader=jinja2.FileSystemLoader(str(BASE / "wrappers")),
    )


def tests_list():
    names = []
    for name in jobs().list_templates(extensions=["jinja2"]):
        if not name.endswith(".yaml.jinja2"):
            continue  # pragma: no cover
        name = name[: -1 * len(".yaml.jinja2")]

        if not name.startswith("tests/"):
            continue
        name = name[len("tests/") :]  # noqa: E203

        if name.startswith("base-"):
            continue
        names.append(name)
    return sorted(names)


def timeouts():
    ret = {}
    for test in tests_list():
        tmpl = jobs().get_template(f"tests/{test}.yaml.jinja2")
        ast = jobs().parse(Path(tmpl.filename).read_text(encoding="utf-8"))
        for node in ast.find_all(jinja2.nodes.Assign):
            if node.target.name == "timeout":
                ret[test] = node.node.value
    return ret
