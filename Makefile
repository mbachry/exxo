.PHONY: clean-build clean build

help:
	@echo "build - build release binary under dist/"
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "release - package and upload a release"
	@echo "dist - package"

build:
	rm -fr env dist/exxo
	python3 -m exxo.exxo venv env
	bash -c "source env/bin/activate && $(shell which python3) -m exxo.exxo build -c"

clean: clean-build clean-test

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

test:
	cd tests && ./run.sh

test-all:
	tox

coverage:
	coverage run --source exxo setup.py test
	coverage report -m
	coverage html

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist
