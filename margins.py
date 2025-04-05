#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: margins.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-04-05 13:35:43

import sys
import textwrap

class FixedWidthStream:
    def __init__(self, width=20):
        self.width = width
        self.buffer = ""

    def write(self, text):
        # Wrap text to the specified width and write to the real stdout
        wrapped = textwrap.fill(text, width=self.width)
        sys.__stdout__.write(wrapped + "\n")

    def flush(self):
        sys.__stdout__.flush()

# Example usage
original_stdout = sys.stdout
sys.stdout = FixedWidthStream(width=20)

# Test it
text = "This is a long string that should wrap sooner than the actual terminal width allows."
print(text)

# Restore original stdout
sys.stdout = original_stdout

# Compare with normal print
print(text)
