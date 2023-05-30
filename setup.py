#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [ ]

test_requirements = [ ]

setup(
    author="Julien Carponcy",
    author_email='juliencarponcy@gmail.com',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9'
    ],
    description="Test package to analyze geospatial soil data for Green Praxis",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='praxis',
    name='praxis',
    packages=find_packages(include=['praxis', 'praxis.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/juliencarponcy/praxis',
    version='0.0.1',
    zip_safe=False,
)
