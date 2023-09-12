lint:
	poetry run isort .
	poetry run black .
	poetry run pydocstyle aineko
	poetry run pylint aineko
	poetry run yamllint -d "{extends: relaxed, ignore-from-file: .gitignore}" .

unit-test:
	poetry run pytest --cov aineko --ignore tests/integration tests/

integration-test:
	poetry run pytest tests/integration