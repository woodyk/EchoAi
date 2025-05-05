#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: themes.py
# Description: Terminal CLI color themes with extended semantic colors for light and dark backgrounds and custom themes.
# Author: Ms. White
# Created: 2025-03-20 13:11:41
# Modified: 2025-05-05 10:00:00

THEMES = {
    "default": {
        "prompt":    "#02788E",  # Teal
        "highlight": "#FFD700",  # Gold
        "error":     "#D9413B",  # Rich Red
        "warning":   "#F5C242",  # Amber
        "info":      "#28A745",  # Emerald Green
        "success":   "#20C997",  # Mint Green
        "output":    "#4D8AFF",  # Cornflower Blue
        "footer":    "#6e757c",  # Gray
        "input":     "#DED300",  # Bright Yellow

        "title":     "#FFD700",  # Gold (table titles)
        "label":     "#02788E",  # Teal (field labels)
        "code":      "#9CDCFE",  # Light Blue (code blocks)
        "dim":       "#6e757c",  # Gray (subdued)
    },
    "dark": {
        "prompt":    "#61AFEF",  # Sky Blue
        "highlight": "#C678DD",  # Lavender
        "error":     "#E06C75",  # Soft Red
        "warning":   "#E5C07B",  # Soft Amber
        "info":      "#98C379",  # Soft Green
        "success":   "#56B6C2",  # Cyan
        "output":    "#ABB2BF",  # Light Gray
        "footer":    "#5C6370",  # Dark Gray
        "input":     "#D19A66",  # Orange

        "title":     "#C678DD",  # Lavender (titles)
        "label":     "#61AFEF",  # Sky Blue (labels)
        "code":      "#ABB2BF",  # Light Gray (code blocks)
        "dim":       "#5C6370",  # Dark Gray (subdued)
    },
    "light": {
        "prompt":    "#005F87",  # Deep Cyan
        "highlight": "#AF00DF",  # Purple
        "error":     "#B00020",  # Deep Red
        "warning":   "#B85C00",  # Warm Orange
        "info":      "#006400",  # Dark Green
        "success":   "#008000",  # Green
        "output":    "#1A1A1A",  # Almost Black
        "footer":    "#999999",  # Medium Gray
        "input":     "#3333AA",  # Indigo

        "title":     "#005F87",  # Deep Cyan (titles)
        "label":     "#AF00DF",  # Purple (labels)
        "code":      "#1A1A1A",  # Almost Black (code blocks)
        "dim":       "#CCCCCC",  # Light Gray (subdued)
    },
    "ocean": {
        "prompt":    "#00CED1",  # Dark Turquoise
        "highlight": "#4682B4",  # Steel Blue
        "error":     "#FF4500",  # Orange Red
        "warning":   "#FFA500",  # Orange
        "info":      "#3CB371",  # Medium Sea Green
        "success":   "#2E8B57",  # Sea Green
        "output":    "#20B2AA",  # Light Sea Green
        "footer":    "#5F9EA0",  # Cadet Blue
        "input":     "#87CEEB",  # Light Sky Blue

        "title":     "#4682B4",  # Steel Blue (titles)
        "label":     "#00CED1",  # Dark Turquoise (labels)
        "code":      "#87CEEB",  # Light Sky Blue (code blocks)
        "dim":       "#5F9EA0",  # Cadet Blue (subdued)
    },
    "forest": {
        "prompt":    "#2E8B57",  # Sea Green
        "highlight": "#9ACD32",  # Yellow Green
        "error":     "#FF6347",  # Tomato
        "warning":   "#DAA520",  # Goldenrod
        "info":      "#228B22",  # Forest Green
        "success":   "#00FF7F",  # Spring Green
        "output":    "#556B2F",  # Dark Olive Green
        "footer":    "#66CDAA",  # Medium Aquamarine
        "input":     "#ADFF2F",  # Green Yellow

        "title":     "#9ACD32",  # Yellow Green (titles)
        "label":     "#2E8B57",  # Sea Green (labels)
        "code":      "#ADFF2F",  # Green Yellow (code blocks)
        "dim":       "#66CDAA",  # Aquamarine (subdued)
    },
    "sunset": {
        "prompt":    "#FFA07A",  # Light Salmon
        "highlight": "#FF69B4",  # Hot Pink
        "error":     "#FF4500",  # Orange Red
        "warning":   "#FFA500",  # Orange
        "info":      "#CD5C5C",  # Indian Red
        "success":   "#32CD32",  # Lime Green
        "output":    "#FFD700",  # Gold
        "footer":    "#FF6347",  # Tomato
        "input":     "#FFDEAD",  # Navajo White

        "title":     "#FF69B4",  # Hot Pink (titles)
        "label":     "#FFA07A",  # Light Salmon (labels)
        "code":      "#FFD700",  # Gold (code blocks)
        "dim":       "#FF6347",  # Tomato (subdued)
    },
    "night": {
        "prompt":    "#B0C4DE",  # Light Steel Blue
        "highlight": "#4682B4",  # Steel Blue
        "error":     "#FF4500",  # Orange Red
        "warning":   "#DAA520",  # Goldenrod
        "info":      "#7CFC00",  # Lawn Green
        "success":   "#00FA9A",  # Medium Spring Green
        "output":    "#708090",  # Slate Gray
        "footer":    "#2F4F4F",  # Dark Slate Gray
        "input":     "#E6E6FA",  # Lavender

        "title":     "#4682B4",  # Steel Blue (titles)
        "label":     "#B0C4DE",  # Light Steel Blue (labels)
        "code":      "#E6E6FA",  # Lavender (code blocks)
        "dim":       "#2F4F4F",  # Dark Slate Gray (subdued)
    },
    "pastel": {
        "prompt":    "#FFB6C1",  # Light Pink
        "highlight": "#AFEEEE",  # Pale Turquoise
        "error":     "#FA8072",  # Salmon
        "warning":   "#FFE4B5",  # Moccasin
        "info":      "#90EE90",  # Light Green
        "success":   "#98FB98",  # Pale Green
        "output":    "#FFFACD",  # Lemon Chiffon
        "footer":    "#D8BFD8",  # Thistle
        "input":     "#E0FFFF",  # Light Cyan

        "title":     "#AFEEEE",  # Pale Turquoise (titles)
        "label":     "#FFB6C1",  # Light Pink (labels)
        "code":      "#E0FFFF",  # Light Cyan (code blocks)
        "dim":       "#D8BFD8",  # Thistle (subdued)
    },
    "solar": {
        "prompt":    "#FFD700",  # Gold
        "highlight": "#FF8C00",  # Dark Orange
        "error":     "#FF4500",  # Orange Red
        "warning":   "#FFA500",  # Orange
        "info":      "#228B22",  # Forest Green
        "success":   "#32CD32",  # Lime Green
        "output":    "#FFDEAD",  # Navajo White
        "footer":    "#FFDAB9",  # Peach Puff
        "input":     "#FFA500",  # Orange

        "title":     "#FF8C00",  # Dark Orange (titles)
        "label":     "#FFD700",  # Gold (labels)
        "code":      "#FFDEAD",  # Navajo White (code blocks)
        "dim":       "#FFDAB9",  # Peach Puff (subdued)
    },
    "lava": {
        "prompt":    "#FF6347",  # Tomato
        "highlight": "#FF4500",  # Orange Red
        "error":     "#8B0000",  # Dark Red
        "warning":   "#FF8C00",  # Dark Orange
        "info":      "#CD5C5C",  # Indian Red
        "success":   "#FFA07A",  # Light Salmon
        "output":    "#FFA07A",  # Light Salmon
        "footer":    "#CD5C5C",  # Indian Red
        "input":     "#FFD700",  # Gold

        "title":     "#FF4500",  # Orange Red (titles)
        "label":     "#FF6347",  # Tomato (labels)
        "code":      "#FFD700",  # Gold (code blocks)
        "dim":       "#CD5C5C",  # Indian Red (subdued)
    },
    "mint": {
        "prompt":    "#98FB98",  # Pale Green
        "highlight": "#66CDAA",  # Medium Aquamarine
        "error":     "#8B0000",  # Dark Red
        "warning":   "#ADFF2F",  # Green Yellow
        "info":      "#2E8B57",  # Sea Green
        "success":   "#20B2AA",  # Light Sea Green
        "output":    "#E0FFFF",  # Light Cyan
        "footer":    "#AFEEEE",  # Pale Turquoise
        "input":     "#F0FFF0",  # Honeydew

        "title":     "#66CDAA",  # Medium Aquamarine (titles)
        "label":     "#98FB98",  # Pale Green (labels)
        "code":      "#E0FFFF",  # Light Cyan (code blocks)
        "dim":       "#AFEEEE",  # Pale Turquoise (subdued)
    },
    "earth": {
        "prompt":    "#8B4513",  # Saddle Brown
        "highlight": "#D2B48C",  # Tan
        "error":     "#A52A2A",  # Brown
        "warning":   "#F4A460",  # Sandy Brown
        "info":      "#228B22",  # Forest Green
        "success":   "#32CD32",  # Lime Green
        "output":    "#DEB887",  # Burlywood
        "footer":    "#8B4513",  # Saddle Brown
        "input":     "#F4A460",  # Sandy Brown

        "title":     "#D2B48C",  # Tan (titles)
        "label":     "#8B4513",  # Saddle Brown (labels)
        "code":      "#DEB887",  # Burlywood (code blocks)
        "dim":       "#8B4513",  # Saddle Brown (subdued)
    },
    "floral": {
        "prompt":    "#FF69B4",  # Hot Pink
        "highlight": "#DB7093",  # Pale Violet Red
        "error":     "#8B0000",  # Dark Red
        "warning":   "#FFC0CB",  # Pink
        "info":      "#BA55D3",  # Medium Orchid
        "success":   "#EE82EE",  # Violet
        "output":    "#FFF0F5",  # Lavender Blush
        "footer":    "#FFB6C1",  # Light Pink
        "input":     "#DDA0DD",  # Plum

        "title":     "#DB7093",  # Pale Violet Red (titles)
        "label":     "#FF69B4",  # Hot Pink (labels)
        "code":      "#FFF0F5",  # Lavender Blush (code blocks)
        "dim":       "#FFB6C1",  # Light Pink (subdued)
    },
    "royal": {
        "prompt":    "#4169E1",  # Royal Blue
        "highlight": "#4682B4",  # Steel Blue
        "error":     "#8B0000",  # Dark Red
        "warning":   "#DAA520",  # Goldenrod
        "info":      "#6A5ACD",  # Slate Blue
        "success":   "#00FF7F",  # Spring Green
        "output":    "#87CEEB",  # Sky Blue
        "footer":    "#B0C4DE",  # Light Steel Blue
        "input":     "#ADD8E6",  # Light Blue

        "title":     "#4682B4",  # Steel Blue (titles)
        "label":     "#4169E1",  # Royal Blue (labels)
        "code":      "#87CEEB",  # Sky Blue (code blocks)
        "dim":       "#B0C4DE",  # Light Steel Blue (subdued)
    },
    "orchid": {
        "prompt":    "#DA70D6",  # Orchid
        "highlight": "#BA55D3",  # Medium Orchid
        "error":     "#9932CC",  # Dark Orchid
        "warning":   "#DDA0DD",  # Plum
        "info":      "#C71585",  # Medium Violet Red
        "success":   "#EE82EE",  # Violet
        "output":    "#E6E6FA",  # Lavender
        "footer":    "#DDA0DD",  # Plum
        "input":     "#FFB6C1",  # Light Pink

        "title":     "#BA55D3",  # Medium Orchid (titles)
        "label":     "#DA70D6",  # Orchid (labels)
        "code":      "#E6E6FA",  # Lavender (code blocks)
        "dim":       "#DDA0DD",  # Plum (subdued)
    },
    "berry": {
        "prompt":    "#C71585",  # Medium Violet Red
        "highlight": "#D87093",  # Pale Violet Red
        "error":     "#8B0000",  # Dark Red
        "warning":   "#FFC0CB",  # Pink
        "info":      "#8A2BE2",  # Blue Violet
        "success":   "#EE82EE",  # Violet
        "output":    "#FFE4E1",  # Misty Rose
        "footer":    "#D8BFD8",  # Thistle
        "input":     "#FF69B4",  # Hot Pink

        "title":     "#D87093",  # Pale Violet Red (titles)
        "label":     "#C71585",  # Medium Violet Red (labels)
        "code":      "#FFE4E1",  # Misty Rose (code blocks)
        "dim":       "#D8BFD8",  # Thistle (subdued)
    },
    "tide": {
        "prompt":    "#00BFFF",  # Deep Sky Blue
        "highlight": "#1E90FF",  # Dodger Blue
        "error":     "#8B0000",  # Dark Red
        "warning":   "#87CEFA",  # Light Sky Blue
        "info":      "#20B2AA",  # Light Sea Green
        "success":   "#3CB371",  # Medium Sea Green
        "output":    "#E0FFFF",  # Light Cyan
        "footer":    "#AFEEEE",  # Pale Turquoise
        "input":     "#B0E0E6",  # Powder Blue

        "title":     "#1E90FF",  # Dodger Blue (titles)
        "label":     "#00BFFF",  # Deep Sky Blue (labels)
        "code":      "#B0E0E6",  # Powder Blue (code blocks)
        "dim":       "#AFEEEE",  # Pale Turquoise (subdued)
    },
    "lemonade": {
        "prompt":    "#FFFACD",  # Lemon Chiffon
        "highlight": "#FFD700",  # Gold
        "error":     "#FF4500",  # Orange Red
        "warning":   "#F5DEB3",  # Wheat
        "info":      "#9ACD32",  # Yellow Green
        "success":   "#32CD32",  # Lime Green
        "output":    "#FFF8DC",  # Cornsilk
        "footer":    "#FAFAD2",  # Light Goldenrod Yellow
        "input":     "#FFD700",  # Gold

        "title":     "#FFD700",  # Gold (titles)
        "label":     "#FFFACD",  # Lemon Chiffon (labels)
        "code":      "#FFF8DC",  # Cornsilk (code blocks)
        "dim":       "#FAFAD2",  # Light Goldenrod Yellow (subdued)
    },
    "slate": {
        "prompt":    "#708090",  # Slate Gray
        "highlight": "#778899",  # Light Slate Gray
        "error":     "#8B0000",  # Dark Red
        "warning":   "#D3D3D3",  # Light Gray
        "info":      "#4682B4",  # Steel Blue
        "success":   "#20B2AA",  # Light Sea Green
        "output":    "#B0C4DE",  # Light Steel Blue
        "footer":    "#2F4F4F",  # Dark Slate Gray
        "input":     "#D3D3D3",  # Light Gray

        "title":     "#778899",  # Light Slate Gray (titles)
        "label":     "#708090",  # Slate Gray (labels)
        "code":      "#B0C4DE",  # Light Steel Blue (code blocks)
        "dim":       "#2F4F4F",  # Dark Slate Gray (subdued)
    },
    "grape": {
        "prompt":    "#9370DB",  # Medium Purple
        "highlight": "#8A2BE2",  # Blue Violet
        "error":     "#8B0000",  # Dark Red
        "warning":   "#DDA0DD",  # Plum
        "info":      "#BA55D3",  # Medium Orchid
        "success":   "#DA70D6",  # Orchid
        "output":    "#DDA0DD",  # Plum
        "footer":    "#9400D3",  # Dark Violet
        "input":     "#E6E6FA",  # Lavender

        "title":     "#8A2BE2",  # Blue Violet (titles)
        "label":     "#9370DB",  # Medium Purple (labels)
        "code":      "#DDA0DD",  # Plum (code blocks)
        "dim":       "#9400D3",  # Dark Violet (subdued)
    },
    "bubblegum": {
        "prompt":    "#FF69B4",  # Hot Pink
        "highlight": "#FF1493",  # Deep Pink
        "error":     "#8B0000",  # Dark Red
        "warning":   "#FFD1DC",  # Pale Pink
        "info":      "#FFB6C1",  # Light Pink
        "success":   "#DB7093",  # Pale Violet Red
        "output":    "#FFC0CB",  # Pink
        "footer":    "#FFB6C1",  # Light Pink
        "input":     "#FFD1DC",  # Pale Pink

        "title":     "#FF1493",  # Deep Pink (titles)
        "label":     "#FF69B4",  # Hot Pink (labels)
        "code":      "#FFC0CB",  # Pink (code blocks)
        "dim":       "#FFB6C1",  # Light Pink (subdued)
    },
    "sky": {
        "prompt":    "#87CEFA",  # Light Sky Blue
        "highlight": "#4682B4",  # Steel Blue
        "error":     "#8B0000",  # Dark Red
        "warning":   "#DAA520",  # Goldenrod
        "info":      "#00CED1",  # Dark Turquoise
        "success":   "#00FA9A",  # Medium Spring Green
        "output":    "#ADD8E6",  # Light Blue
        "footer":    "#87CEEB",  # Sky Blue
        "input":     "#E0FFFF",  # Light Cyan

        "title":     "#4682B4",  # Steel Blue (titles)
        "label":     "#87CEFA",  # Light Sky Blue (labels)
        "code":      "#ADD8E6",  # Light Blue (code blocks)
        "dim":       "#87CEEB",  # Sky Blue (subdued)
    },
    "hacker": {
        "prompt":    "#00FF00",  # Neon Green
        "highlight": "#FF00FF",  # Neon Magenta
        "error":     "#FF0000",  # Bright Red
        "warning":   "#FFFF00",  # Neon Yellow
        "info":      "#00FFFF",  # Cyan
        "success":   "#00FF7F",  # Spring Green
        "output":    "#00FFFF",  # Cyan
        "footer":    "#555555",  # Dark Gray
        "input":     "#FFFF00",  # Neon Yellow

        "title":     "#FF00FF",  # Neon Magenta (titles)
        "label":     "#00FF00",  # Neon Green (labels)
        "code":      "#00FFFF",  # Cyan (code blocks)
        "dim":       "#555555",  # Dark Gray (subdued)
    },
    "bright": {
        "prompt":    "#FF00FF",  # Neon Magenta
        "highlight": "#FFFF00",  # Neon Yellow
        "error":     "#FF0000",  # Bright Red
        "warning":   "#FFA500",  # Bright Orange
        "info":      "#00FFFF",  # Bright Cyan
        "success":   "#00FF00",  # Bright Lime
        "output":    "#FFFFFF",  # White
        "footer":    "#888888",  # Gray
        "input":     "#FFFFFF",  # White

        "title":     "#FFFF00",  # Neon Yellow (titles)
        "label":     "#FF00FF",  # Neon Magenta (labels)
        "code":      "#FFFFFF",  # White (code blocks)
        "dim":       "#777777",  # Dim Gray (subdued)
    },
}

if __name__ == "__main__":
    from rich.console import Console
    console = Console()
    for theme_name, colors in THEMES.items():
        console.rule(f"[bold]{theme_name} Theme[/bold]", style=colors.get("title", colors["highlight"]))
        for key, hexcode in colors.items():
            console.print(f"[{hexcode}]{key:<10} sample text[/{hexcode}]")
        console.print()

