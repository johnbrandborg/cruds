help:  # Displays the help menu with all the targets
	@grep -E '^[a-zA-Z0-9 -]+:.*#' Makefile | while read -r l; do \
		printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; \
		done

apidocs:  # Creates API documentation for RTDs
	@uv run sphinx-apidoc -f -o docs cruds/

develop:  # Installs all requirements and testing requirements
	@uv sync --group dev \
		&& uv run pre-commit install

test:  # Perform unit testing on the source code
	@uv run pytest -vvv

test-report:  # Perform unit testing on the source code with a coverage report
	@uv run pytest --cov-report=xml

lint:  # Quality checks on the source code (Doesn't change code)
	@uv run ruff check --diff src/

format:  # Check the format of source code  (Doesn't change code)
	@uv run ruff format --diff src/

typecheck:  # Static type checking on the source code
	@uv run ty check

uninstall: clean
	@uv pip uninstall cruds

clean:  # Removes built Python Packages and cached byte code
	@find . -type d -name __pycache__ -prune -exec rm -rfv {} \;;\
		find . -type d -name '*.egg-info' -prune -exec rm -rfv {} \;;\
		echo "clean completed"

.DEFAULT_GOAL := help
.PHONY: help apidocs develop test test-report lint format typecheck uninstall clean
