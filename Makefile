.PHONY: build clean test install

# Clean build artifacts
clean:
	rm -rf build dist *.egg-info

# Run tests
test:
	pytest tests

# Build the package (assumes tests have already been run)
build: clean test
	python setup.py sdist bdist_wheel

# Install the package
install:
	pip install dist/*.whl
