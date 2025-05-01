#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: themes.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-20 13:11:41
# Modified: 2025-04-30 19:50:19

themes = {
    "default": {
        "prompt": "#02788E",        # Teal
        "highlight": "#FFD700",
        "error": "#FF0000",
        "output": "#4D8AFF",
        "footer": "#6e757c",
        "input": "#DED300"         # Bright Yellow (unchanged)
    },
    "ocean": {
        "prompt": "#00CED1",   # Dark Turquoise
        "highlight": "#4682B4",     # Steel Blue
        "error": "#FF4500",
        "output": "#20B2AA",
        "footer": "#5F9EA0",
        "input": "#87CEEB"         # Light Sky Blue (lighter, airy contrast)
    },
    "forest": {
        "prompt": "#2E8B57",   # Sea Green
        "highlight": "#9ACD32",
        "error": "#FF6347",
        "output": "#556B2F",
        "footer": "#66CDAA",
        "input": "#ADFF2F"         # Green Yellow (bright, earthy contrast)
    },
    "sunset": {
        "prompt": "#FFA07A",   # Light Salmon
        "highlight": "#FF69B4",
        "error": "#FF4500",
        "output": "#FFD700",
        "footer": "#FF6347",
        "input": "#FFDEAD"         # Navajo White (soft, warm contrast)
    },
    "night": {
        "prompt": "#B0C4DE",   # Light Steel Blue
        "highlight": "#4682B4",
        "error": "#FF4500",
        "output": "#708090",
        "footer": "#2F4F4F",
        "input": "#E6E6FA"         # Lavender (light, starry contrast)
    },
    "pastel": {
        "prompt": "#FFB6C1",   # Light Pink
        "highlight": "#AFEEEE",
        "error": "#FA8072",
        "output": "#FFFACD",
        "footer": "#D8BFD8",
        "input": "#E0FFFF"         # Light Cyan (soft, pastel contrast)
    },
    "solar": {
        "prompt": "#FFD700",   # Gold
        "highlight": "#FF8C00",
        "error": "#FF4500",
        "output": "#FFDEAD",
        "footer": "#FFDAB9",
        "input": "#FFA500"         # Orange (vibrant, sunny contrast)
    },
    "lava": {
        "prompt": "#FF6347",   # Tomato
        "highlight": "#FF4500",
        "error": "#8B0000",
        "output": "#FFA07A",
        "footer": "#CD5C5C",
        "input": "#FFD700"         # Gold (fiery, glowing contrast)
    },
    "mint": {
        "prompt": "#98FB98",   # Pale Green
        "highlight": "#66CDAA",
        "error": "#8B0000",
        "output": "#E0FFFF",
        "footer": "#AFEEEE",
        "input": "#F0FFF0"         # Honeydew (crisp, minty contrast)
    },
    "earth": {
        "prompt": "#8B4513",   # Saddle Brown
        "highlight": "#D2B48C",
        "error": "#A52A2A",
        "output": "#DEB887",
        "footer": "#8B4513",
        "input": "#F4A460"         # Sandy Brown (warm, earthy contrast)
    },
    "floral": {
        "prompt": "#FF69B4",   # Hot Pink
        "highlight": "#DB7093",
        "error": "#8B0000",
        "output": "#FFF0F5",
        "footer": "#FFB6C1",
        "input": "#DDA0DD"         # Plum (soft, floral contrast)
    },
    "royal": {
        "prompt": "#4169E1",   # Royal Blue
        "highlight": "#4682B4",
        "error": "#8B0000",
        "output": "#87CEEB",
        "footer": "#B0C4DE",
        "input": "#ADD8E6"         # Light Blue (regal, cool contrast)
    },
    "orchid": {
        "prompt": "#DA70D6",   # Orchid
        "highlight": "#BA55D3",
        "error": "#9932CC",
        "output": "#E6E6FA",
        "footer": "#DDA0DD",
        "input": "#FFB6C1"         # Light Pink (delicate, floral contrast)
    },
    "berry": {
        "prompt": "#C71585",   # Medium Violet Red
        "highlight": "#D87093",
        "error": "#8B0000",
        "output": "#FFE4E1",
        "footer": "#D8BFD8",
        "input": "#FF69B4"         # Hot Pink (vibrant, berry-like contrast)
    },
    "tide": {
        "prompt": "#00BFFF",   # Deep Sky Blue
        "highlight": "#1E90FF",
        "error": "#8B0000",
        "output": "#E0FFFF",
        "footer": "#AFEEEE",
        "input": "#B0E0E6"         # Powder Blue (soft, watery contrast)
    },
    "lemonade": {
        "prompt": "#FFFACD",   # Lemon Chiffon
        "highlight": "#FFD700",
        "error": "#FF4500",
        "output": "#FFF8DC",
        "footer": "#FAFAD2",
        "input": "#FFD700"         # Gold (bright, citrusy contrast)
    },
    "slate": {
        "prompt": "#708090",   # Slate Gray
        "highlight": "#778899",
        "error": "#8B0000",
        "output": "#B0C4DE",
        "footer": "#2F4F4F",
        "input": "#D3D3D3"         # Light Gray (clean, slate contrast)
    },
    "grape": {
        "prompt": "#9370DB",   # Medium Purple
        "highlight": "#8A2BE2",
        "error": "#8B0000",
        "output": "#DDA0DD",
        "footer": "#9400D3",
        "input": "#E6E6FA"         # Lavender (light, grapey contrast)
    },
    "bubblegum": {
        "prompt": "#FF69B4",   # Hot Pink
        "highlight": "#FF1493",
        "error": "#8B0000",
        "output": "#FFC0CB",
        "footer": "#FFB6C1",
        "input": "#FFD1DC"         # Pale Pink (sweet, bubbly contrast)
    },
    "sky": {
        "prompt": "#87CEFA",   # Light Sky Blue
        "highlight": "#4682B4",
        "error": "#8B0000",
        "output": "#ADD8E6",
        "footer": "#87CEEB",
        "input": "#E0FFFF"         # Light Cyan (airy, sky contrast)
    },
    "hacker": {
        "prompt": "#00FF00",   # Neon Green (classic hacker green)
        "highlight": "#FF00FF",     # Neon Magenta (cyberpunk highlight)
        "error": "#FF0000",    # Bright Red (alerting error)
        "output": "#00FFFF",        # Cyan (data output)
        "footer": "#555555",        # Dark Gray (subtle footer)
        "input": "#FFFF00"         # Neon Yellow (contrasting input)
    },
}
