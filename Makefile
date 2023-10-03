help:
	@echo "lint - lint code"
	@echo "unit-test - run unit tests suite"
	@echo "integration-test - run integration tests suite"

lint:
	poetry run isort .
	poetry run black .
	poetry run pydocstyle aineko
	poetry run pylint aineko
	poetry run yamllint -c yamllint.yaml .
	poetry run mypy aineko
	poetry run pre-commit run --all

unit-test:
	poetry run pytest --cov aineko --ignore tests/integration tests/

integration-test:
	docker-compose up -d
	poetry run pytest tests/integration
