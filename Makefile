test:
	@python -m pytest

lint:
	@python -m flake8 --select=E9,F63,F7,F82 --show-source

develop:
	@python -m pip install -e .[develop]

uninstall: clean
	@pip uninstall -y cruds

clean:
	@python -c "from setuptools import setup; setup()" clean --all;\
		find $(PACKAGES) -type d -name __pycache__ -prune -exec rm -rfv {} \;;\
		find $(PACKAGES) -type d -name '*.egg-info' -prune -exec rm -rfv {} \;;\
		echo "clean completed"

help:
	@echo "\
Targets\n\
------------------------------------------------------------------------\n\
 test:		Perform unit testing on the source code\n\
 lint:		Perform quality checks on the source code\n\
 develop:	Installs all requirements and testing requirements\n\
 clean:		Removes built Python Packages and cached byte code\n\
 help:		Displays the help menu with all the targets\n";

.DEFAULT_GOAL := help
.PHONY: test lint develop clean help
