help:
	@echo "lint - lint code"
	@echo "lint-docs - lint documentation"
	@echo "unit-test - run unit tests suite"
	@echo "integration-test - run integration tests suite"
	@echo "install-dev - install all dependencies for development"
	@echo "view-docs - run a local server to view documentation"

install-dev:
	poetry install --with dev,docs,test --all-extras

lint:
	@ERROR=0; \
	poetry run isort . || ERROR=1; \
	poetry run black . --exclude .*{{cookiecutter.project_slug}}\/tests\/.*.py || ERROR=1; \
	poetry run pydocstyle aineko || ERROR=1; \
	poetry run pylint aineko || ERROR=1; \
	poetry run yamllint -c yamllint.yaml . || ERROR=1; \
	poetry run mypy aineko || ERROR=1; \
	poetry run pre-commit run --all || ERROR=1; \
	exit $$ERROR

lint-docs:
	vale sync
	vale --glob="[!.]*.{md,adoc}" --config=.vale.ini .

unit-test:
	poetry run pytest --cov aineko -m "not integration" tests

integration-test:
	poetry run aineko service start
	poetry run pytest tests -m "integration"

view-docs:
	poetry run mkdocs serve
