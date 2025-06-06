#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: display_image.py
# Author: Ms. White 
# Description: Terminal image display via Kitty graphics protocol with preserved aspect ratio
# Created: 2025-05-01
# Modified: 2025-05-17 16:59:58

import os
import sys
import json
from base64 import standard_b64encode
from typing import Dict, Union
from rich.console import Console

console = Console()
print = console.print

def display_image(image_path: str, image_size_in_percent: Union[int, str] = 30) -> Dict[str, str]:
    """Display an image in the terminal using the Kitty graphics protocol, preserving aspect ratio.

    Scales the image to a target terminal column width, then computes row count using pixel aspect
    ratio correction (typically 2:1 height:width per terminal cell). Designed for Kitty-compatible
    terminals and CLI environments.

    Args:
        image_path (str): Path to the image file.
        image_size_in_percent (Union[int, str], optional): Width as a percent of terminal columns (1–100).
            Defaults to 30.

    Returns:
        Dict[str, str]: A response object with:
            - status (str): "success" or "error"
            - image_path (str): The image path
            - error (str, optional): Reason for failure if any
    """
    def serialize_gr_command(**cmd):
        payload = cmd.pop('payload', None)
        cmd_str = ','.join(f'{k}={v}' for k, v in cmd.items())
        return b''.join([b'\033_G', cmd_str.encode('ascii'), b';' if payload else b'', payload or b'', b'\033\\'])

    def write_chunked(**cmd):
        data = standard_b64encode(cmd.pop('data'))
        while data:
            chunk, data = data[:4096], data[4096:]
            m = 1 if data else 0
            sys.stdout.buffer.write(serialize_gr_command(payload=chunk, m=m, **cmd))
            sys.stdout.flush()
            cmd.clear()

    try:
        if not os.path.isfile(image_path):
            return {
                "status": "error",
                "image_path": image_path,
                "error": "File not found"
            }

        try:
            size_percent = int(image_size_in_percent)
            if not (1 <= size_percent <= 100):
                raise ValueError
        except ValueError:
            return {
                "status": "error",
                "image_path": image_path,
                "error": "Image size percent must be an integer between 1 and 100"
            }

        try:
            from PIL import Image
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except Exception as e:
            return {
                "status": "error",
                "image_path": image_path,
                "error": f"Failed to read image metadata: {str(e)}"
            }

        # Terminal dimensions
        term_cols = console.size.width
        target_cols = max(1, int(term_cols * size_percent / 100))

        # Compensate for cell aspect ratio (height is ~2x width)
        aspect_ratio = img_height / img_width
        target_rows = max(1, int(target_cols * aspect_ratio * 0.5))

        with open(image_path, 'rb') as f:
            write_chunked(a='T', f=100, c=target_cols, r=target_rows, data=f.read())

        print()

        return {
            "status": "success",
            "image_path": image_path
        }

    except Exception as e:
        return {
            "status": "error",
            "image_path": image_path,
            "error": f"Unexpected error: {str(e)}"
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[yellow]Usage: python display_image.py <image_path> [size_percent][/yellow]")
        sys.exit(1)

    image_path = sys.argv[1]
    size_percent = sys.argv[2] if len(sys.argv) > 2 else 30
    result = display_image(image_path, size_percent)
    print(json.dumps(result, indent=2))

