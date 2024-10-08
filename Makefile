help:  # Displays the help menu with all the targets
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

apidocs:  # Creates API documentation for RTDs
	@sphinx-apidoc -f -o docs cruds/

test:  # Perform unit testing on the source code
	@python -m pytest

test-report:  # Perform unit testing on the source code with a coverage report
	@python -m pytest --cov-report=xml

lint:  # Perform quality checks on the source code
	# stop the build if there are Python syntax errors or undefined names
	@python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	@python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

develop:  update-pip  # Installs all requirements and testing requirements
	@python -m pip install -e '.[develop]'

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
.PHONY: docs test lint develop clean help
