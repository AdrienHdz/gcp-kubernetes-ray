.PHONY: install
install: 
	pip install --upgrade pip &&\
	{ pip freeze | grep pip-tools > /dev/null || pip install pip-tools ; }
	pip-compile requirements.in &&\
	pip-sync requirements.txt

.PHONY: test
test:
	# python -m pytest -vv --cov=main parallelize_torch/test/test_*.py

.PHONY: format
format:
	find parallelize_torch parallelize_xgboost -type f -name '*.py' -exec black {} +

.PHONY: lint
lint:
	find parallelize_torch parallelize_xgboost -type f -name '*.py' -exec ruff check {} +

.PHONY: typing
typing:
	find parallelize_torch parallelize_xgboost -type -name '*.py' -exec mypy --implicit-optional {} +

.PHONY: refactor
refactor: format lint typing 

.PHONY: all
all: install format lint test  