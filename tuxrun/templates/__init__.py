from pathlib import Path

import jinja2


BASE = (Path(__file__) / "..").resolve()

jobs = jinja2.Environment(
    autoescape=False,
    loader=jinja2.FileSystemLoader(str(BASE / "jobs")),
)

devices = jinja2.Environment(
    autoescape=False,
    loader=jinja2.FileSystemLoader(str(BASE / "devices")),
)
