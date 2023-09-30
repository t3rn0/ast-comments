PYTHON_VERSION = $(shell python -c "import sys;print('{v[0]}.{v[1]}'.format(v=sys.version_info[:2]))")
TEST_CODE = test_parse.py test_unparse.py
CODE = ast_comments.py
ALL_CODE = $(CODE) $(TEST_CODE)

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: format
format:	## format code
	isort $(ALL_CODE)
	black $(ALL_CODE)

.PHONY: lint
lint:	## lint code
	flake8 $(ALL_CODE) --config ./setup.cfg
	black --check $(ALL_CODE) 

.PHONY: test
test:	## test code
	@if [[ $(PYTHON_VERSION) = 3.8 ]]; then \
		pytest test_parse.py; \
	else \
		pytest $(TEST_CODE); \
	fi

.PHONY: check
check: lint test	## check
