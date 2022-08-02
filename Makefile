.PHONY: format
format:
	isort .
	black .

.PHONY: lint
lint:
	flake8 *.py --config ./pyproject.toml

.PHONY: test
test:
	pytest .


.PHONY: check
check: lint test