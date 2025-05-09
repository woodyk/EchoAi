#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: crucial_remote.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-05-08 18:35:02
# Modified: 2025-05-08 20:31:50

import json
import urllib.request
from rich.console import Console

console = Console()
print = console.print

try:
    # Load all remote tool functions (including create, draw_line, etc.)
    url = "http://localhost:8000/python"
    exec(urllib.request.urlopen(url).read().decode())
except:
    pass

def main():
    # Step 1: Create a canvas (adjust name, size, color as desired)
    canvas = canvas_create(
        name="Remote Test",
        x=800,
        y=600,
        color="#111111"
    )

    print(canvas)
    canvas_id = canvas["canvas_id"]

    # Step 2: Draw a line using the returned canvas_id
    response = canvas_draw_line(
        canvas_id=canvas_id,
        start_x=10,
        start_y=20,
        end_x=300,
        end_y=200,
        color="#ff00ff",
        width=4
    )

    print(response)

    print(f"{BASE_URL}/canvas/{canvas_id}")

if __name__ == "__main__":
    main()
