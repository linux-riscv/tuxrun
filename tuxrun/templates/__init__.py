from pathlib import Path

import jinja2


BASE = (Path(__file__) / "..").resolve()

jobs = jinja2.Environment(
    autoescape=False,
    trim_blocks=True,
    loader=jinja2.FileSystemLoader(str(BASE / "jobs")),
)

devices = jinja2.Environment(
    autoescape=False,
    trim_blocks=True,
    loader=jinja2.FileSystemLoader(str(BASE / "devices")),
)
