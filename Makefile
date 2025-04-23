## Makefile
pythonfiles = *.py modules/*.py

flake8: $(pythonfiles)
	flake8 --ignore=E501 $(pythonfiles)

pylint: $(pythonfiles)
	pylint --disable=line-too-long $(pythonfiles)

build: Dockerfile lint ## build docker container
	docker build -t pmaxperfpy .

.PHONY: lint test help

.DEFAULT_GOAL := help

lint: flake8 pylint ## code linting (checking)

test: lint ## run code tests

help: ## this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-30s %s\n", $$1, $$2}'

