export PROJECT := tuxrun

test: typecheck unit-tests spellcheck stylecheck

COVERAGE = 94.35

unit-tests:
	python3 -m pytest \
		--cov=tuxrun \
		--cov-report=term-missing \
		--cov-fail-under=$(COVERAGE) \
		test

.PHONY: htmlcov tags

htmlcov:
	python3 -m pytest --cov=tuxrun --cov-report=html

stylecheck:
	black --check --diff .
	flake8 .

typecheck:
	mypy tuxrun

spellcheck:
	codespell \
		--check-filenames \
		--skip '.git,public,dist,*.sw*,*.pyc,tags,*.json,.coverage,htmlcov,*.jinja2'

integration:
	python3 test/integration.py

doc: docs/index.md
	mkdocs build

docs/index.md: README.md scripts/readme2index.sh
	scripts/readme2index.sh $@

doc-serve:
	mkdocs serve

flit = flit
publish-pypi:
	$(flit) publish

release:
	flit=true scripts/release $(V)

tags:
	ctags -R tuxrun/ test/
