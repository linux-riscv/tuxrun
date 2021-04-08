test: typecheck spellcheck stylecheck unit-tests

unit-tests:
	python3 -m pytest --cov=tuxrun --cov-report=term-missing --cov-fail-under=39 test

stylecheck:
	black --check --diff .
	flake8 .

typecheck:
	mypy tuxrun

spellcheck:
	codespell \
		--check-filenames \
		--skip '.git,public,dist,*.sw*,*.pyc,tags,*.json,.coverage,htmlcov'

doc:
	mkdocs build

doc-serve:
	mkdocs serve

flit = flit
publish-pypi:
	$(flit) publish
