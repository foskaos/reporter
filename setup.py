from setuptools import setup, find_packages

setup(
    name='reporter_cli',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'jinja2',
        'pytest'
    ],
    include_package_data=True,  # Include package data
    package_data={
        'reporter_cli': ['templates/*'],
    },
    entry_points={
        'console_scripts': [
            'reporter=reporter_cli.cli:cli',  # Adjust based on your cli entry point
        ],
    },
    test_suite='tests',
    tests_require=[
        'pytest',
    ],
)
