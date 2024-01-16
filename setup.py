#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', 'pandas', 'pyparsing>=3.0.0', 'scikit-learn', 'numpy']

test_requirements = [ ]

setup(
    author="Willem Jan Willemse",
    author_email='w.j.willemse@xs4all.nl',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python package to mine association rules in datasets",
    entry_points={
        'console_scripts': [
            'ruleminer=ruleminer.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='ruleminer',
    name='ruleminer',
    packages=find_packages(include=['ruleminer', 'ruleminer.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/wjwillemse/ruleminer',
    version='0.1.25',
    zip_safe=False,
)
