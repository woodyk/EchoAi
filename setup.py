#!/usr/bin/env python3
#
# setup.py

from setuptools import setup, find_packages

setup(
    name="echoai",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-docx",
        "openai",
        "prompt_toolkit",
        "PyPDF2",
        "python_magic",
        "rich",
        "ollama",
        "setuptools",
    ],
    entry_points={
        'console_scripts': [
            'echoai=echoai.main:main',  # Format: command=package.module:function
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
    python_requires='>=3.7',  # Set your required Python version here
)
