test: typecheck unit-tests spellcheck stylecheck

unit-tests:
	python3 -m pytest --cov=tuxrun --cov-report=term-missing --cov-fail-under=71 test

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
		--skip '.git,public,dist,*.sw*,*.pyc,tags,*.json,.coverage,htmlcov'

doc:
	mkdocs build

doc-serve:
	mkdocs serve

flit = flit
publish-pypi:
	$(flit) publish
