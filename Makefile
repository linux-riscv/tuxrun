export PROJECT := tuxrun

test: typecheck unit-tests spellcheck stylecheck

COVERAGE = 92.08

unit-tests:
	python3 -m pytest \
		--cov=tuxrun \
		--cov-report=term-missing \
		--cov-fail-under=$(COVERAGE) \
		test

.PHONY: htmlcov

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

doc:
	mkdocs build

doc-serve:
	mkdocs serve

flit = flit
publish-pypi:
	$(flit) publish

release:
	flit=true scripts/release $(V)
