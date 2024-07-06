format:
	black .
	isort .

lint:
	mypy .
	flake8 .

check-formatting:
	black . --check
	isort . --check

check-linting:
	mypy .
	flake8 .
