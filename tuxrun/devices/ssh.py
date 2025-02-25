# vim: set ts=4
#
# Copyright 2021-present Linaro Limited
#
# SPDX-License-Identifier: MIT

from tuxrun import templates
from tuxrun.devices import Device
from tuxrun.exceptions import InvalidArgument
from tuxrun.utils import notnone, slugify


class SSHDevice(Device):
    name = "ssh-device"
    ssh_port = 22

    def validate(
        self,
        commands,
        tests,
        parameters,
        overlays,
        ssh_host,
        ssh_port,
        ssh_prompt,
        ssh_user,
        ssh_identity_file,
        **kwargs,
    ):
        invalid_args = ["--" + k.replace("_", "-") for k in kwargs if kwargs[k]]
        if len(invalid_args) > 0:
            raise InvalidArgument(
                f"Invalid option(s) for ssh device: {', '.join(sorted(invalid_args))}"
            )
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_identity_file = ssh_identity_file.replace("file://", "")

    def default(self, options) -> None:
        options.ssh_port = notnone(options.ssh_port, self.ssh_port)

    def definition(self, **kwargs):
        # Options that can be updated
        if kwargs["ssh_prompt"]:
            kwargs["ssh_prompt"] = [kwargs["ssh_prompt"]]
        else:
            kwargs["ssh_prompt"] = []

        kwargs["command_name"] = slugify(
            kwargs.get("parameters").get("command-name", "command")
        )

        # render the template
        tests = [
            t.render(
                arch="arm64",
                commands=kwargs["commands"],
                command_name=kwargs["command_name"],
                device=kwargs["device"],
                tmpdir=kwargs["tmpdir"],
                ssh_prompt=kwargs["ssh_prompt"],
                overlays=kwargs["overlays"],
                parameters=kwargs["parameters"],
                test_definitions=kwargs["test_definitions"],
            )
            for t in kwargs["tests"]
        ]
        return templates.jobs().get_template("ssh.yaml.jinja2").render(
            **kwargs
        ) + "".join(tests)

    def device_dict(self, context):
        context["ssh_host"] = self.ssh_host
        context["ssh_user"] = self.ssh_user
        context["ssh_port"] = self.ssh_port
        context["ssh_identity_file"] = f"{self.ssh_identity_file}"
        context["lava_test_results_dir"] = "/tmp/lava-%s"
        return templates.devices().get_template("ssh.yaml.jinja2").render(**context)
