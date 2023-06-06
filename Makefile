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
	find main -type f -name '*.py' -exec black {} +

.PHONY: lint
lint:
	find main -type f -name '*.py' -exec pylint --disable=R,C {} +

.PHONY: refactor
refactor: format lint

.PHONY: all
all: install lint test format 