test: unit-tests stylecheck typecheck spellcheck

unit-tests:
	python3 -m pytest --cov=tuxrun --cov-report=term-missing --cov-fail-under=100 test

stylecheck:
	black --check --diff .
	flake8 .

typecheck:
	mypy tuxrun

spellcheck:
	codespell \
		--check-filenames \
		--skip '.git,public,dist,*.sw*,*.pyc,tags,*.json,.coverage,htmlcov'
