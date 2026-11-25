.PHONY: install test fetch verify run all clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

fetch:
	nhs-ghg fetch

verify:
	nhs-ghg verify

run:
	nhs-ghg run

all: install fetch verify test run
