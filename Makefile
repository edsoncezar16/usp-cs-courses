.PHONY: ruff dev_install config dagster

dagster: config
	DAGSTER_HOME=$(shell pwd) dagster dev

config: setup
	generate-assets-config

setup:
	pip install -e .[dev]
	pre-commit install
