#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: setup.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-24 16:48:15
# Modified: 2025-06-22 18:05:29

from setuptools import setup, find_packages

def load_requirements(filename):
    with open(filename, 'r') as req_file:
        return [line.strip() for line in req_file if line.strip() and not line.startswith("#")]

setup(
    name="echoai",
    version="1.1.5",
    packages=find_packages(),
    install_requires=load_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'echoai=echoai.main:main',
            'ai=echoai.main:main',
        ],
    },
    author="Wadih Khairallah",
    author_email="woodyk@gmail.com",
    description="A command-line AI chatbot",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/woodyk/echoai",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='3.12',
)
