help:
	@echo "lint - lint code"
	@echo "unit-test - run unit tests suite"
	@echo "integration-test - run integration tests suite"

lint:
	@ERROR=0; \
	poetry run isort . || ERROR=1; \
	poetry run black . || ERROR=1; \
	poetry run pydocstyle aineko || ERROR=1; \
	poetry run pylint aineko || ERROR=1; \
	poetry run yamllint -c yamllint.yaml . || ERROR=1; \
	poetry run mypy aineko || ERROR=1; \
	poetry run pre-commit run --all || ERROR=1; \
	exit $$ERROR

unit-test:
	poetry run pytest --cov aineko --ignore tests/integration tests/

integration-test:
	poetry run aineko service start
	poetry run pytest tests/integration
