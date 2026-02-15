run:
	poetry run python src/script.py

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run mypy src/
	poetry run flake8 .

format-ci:
	poetry run black . --check
	poetry run isort . --check

lint-ci:
	poetry run mypy src/
	poetry run flake8 .

test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html

test-ci-cov:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=80
