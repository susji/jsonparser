#
# NB: Expects Python 3.6 or later and Mypy.
#
PYTHON ?= python3
MYPY ?= $(shell which mypy)
TEST := -m unittest discover -v jsonparser
COVERAGE ?= coverage3

test:
	@echo Python: $(PYTHON)
	@echo mypy: $(MYPY)
	$(PYTHON) $(TEST)
	$(PYTHON) $(MYPY) jsonparser

coverage:
	$(COVERAGE) run $(TEST)
	$(COVERAGE) report

.PHONY: test coverage

