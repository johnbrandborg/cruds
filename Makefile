help:  # Displays the help menu with all the targets
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

apidocs:  # Creates API documentation for RTDs
	@sphinx-apidoc -f -o docs cruds/

develop:  update-pip  # Installs all requirements and testing requirements
	@python -m pip install -e '.[develop]' \
		&& pre-commit install

test:  # Perform unit testing on the source code
	@python -m pytest -vvv

test-report:  # Perform unit testing on the source code with a coverage report
	@python -m pytest --cov-report=xml

lint:  # Quality checks on the source code (Doesn't change code)
	@python -m ruff check --diff src/

format:  # Check the format of source code  (Doesn't change code)
	@python -m ruff format --diff src/

update-pip:  # Updates the version of pip
	@python -m pip install --upgrade pip

uninstall: clean
	@pip uninstall -y cruds

clean:  # Removes built Python Packages and cached byte code
	@python -c "from setuptools import setup; setup()" clean --all;\
		find $(PACKAGES) -type d -name __pycache__ -prune -exec rm -rfv {} \;;\
		find $(PACKAGES) -type d -name '*.egg-info' -prune -exec rm -rfv {} \;;\
		echo "clean completed"

.DEFAULT_GOAL := help
.PHONY: help apidocs develop test test-report lint format update-pip uninstall clean
