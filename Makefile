lint:
	poetry run isort .
	poetry run black .
	poetry run pydocstyle aineko
	poetry run pylint aineko
	poetry run yamllint -d "{extends: relaxed, ignore-from-file: .gitignore}" .
	poetry run mypy aineko
	poetry run pre-commit run --all

unit-test:
	poetry run pytest --cov aineko --ignore tests/integration tests/

integration-test:
	docker-compose up -d
	poetry run pytest tests/integration
