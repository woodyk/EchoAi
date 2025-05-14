#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: themes.py
# Description: Terminal CLI color themes with extended semantic colors for light and dark backgrounds and custom themes.
# Author: Ms. White
# Created: 2025-03-20 13:11:41
# Modified: 2025-05-13 21:55:45

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

        # Role colors
        "user":      "#3A7D7A",  # Deep Teal
        "assistant": "#0F94A3",  # Bright Teal
        "system":    "#5A6268",  # Slate Gray
        "tool":      "#4D8AFF",  # Cornflower Blue

        # UI elements
        "border":          "#CCCCCC",  # Light Gray
        "border_focused":  "#02788E",  # Teal
        "card":            "#FFFFFF",  # White
        "modal":           "#F8F9FA",  # Off-White
        "button":          "#02788E",  # Teal
        "button_focused":  "#016577",  # Darker Teal
        "text":            "#212529",  # Near Black
        "subtext":         "#6e757c",  # Gray
        "body":            "#F8F9FA",  # Off-White
        "disabled":        "#DEE2E6",  # Light Gray
        "active":          "#20C997",  # Mint Green
        "primary":         "#02788E",  # Teal
        "secondary":       "#6e757c",  # Gray
        "tertiary":        "#F5C242",  # Amber
        "background":      "#FFFFFF",  # White
        "foreground":      "#212529",  # Near Black
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

        # Role colors
        "user":      "#56B6C2",  # Cyan
        "assistant": "#61AFEF",  # Sky Blue
        "system":    "#5C6370",  # Dark Gray
        "tool":      "#98C379",  # Soft Green

        # UI elements
        "border":          "#4B5263",  # Medium Gray
        "border_focused":  "#61AFEF",  # Sky Blue
        "card":            "#282C34",  # Dark Blue-Gray
        "modal":           "#3E4451",  # Medium Blue-Gray
        "button":          "#61AFEF",  # Sky Blue
        "button_focused":  "#528BFF",  # Bright Blue
        "text":            "#ABB2BF",  # Light Gray
        "subtext":         "#5C6370",  # Dark Gray
        "body":            "#282C34",  # Dark Blue-Gray
        "disabled":        "#4B5263",  # Medium Gray
        "active":          "#56B6C2",  # Cyan
        "primary":         "#61AFEF",  # Sky Blue
        "secondary":       "#C678DD",  # Lavender
        "tertiary":        "#E5C07B",  # Soft Amber
        "background":      "#1E2127",  # Near Black
        "foreground":      "#ABB2BF",  # Light Gray
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

        # Role colors
        "user":      "#3333AA",  # Indigo
        "assistant": "#005F87",  # Deep Cyan
        "system":    "#999999",  # Medium Gray
        "tool":      "#006400",  # Dark Green

        # UI elements
        "border":          "#E0E0E0",  # Light Gray
        "border_focused":  "#005F87",  # Deep Cyan
        "card":            "#FFFFFF",  # White
        "modal":           "#F5F5F5",  # Lightest Gray
        "button":          "#005F87",  # Deep Cyan
        "button_focused":  "#004D70",  # Darker Cyan
        "text":            "#1A1A1A",  # Almost Black
        "subtext":         "#999999",  # Medium Gray
        "body":            "#FAFAFA",  # Off-White
        "disabled":        "#E0E0E0",  # Light Gray
        "active":          "#008000",  # Green
        "primary":         "#005F87",  # Deep Cyan
        "secondary":       "#AF00DF",  # Purple
        "tertiary":        "#B85C00",  # Warm Orange
        "background":      "#FFFFFF",  # White
        "foreground":      "#1A1A1A",  # Almost Black
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

        # Role colors
        "user":      "#4682B4",  # Steel Blue
        "assistant": "#00CED1",  # Dark Turquoise
        "system":    "#5F9EA0",  # Cadet Blue
        "tool":      "#3CB371",  # Medium Sea Green

        # UI elements
        "border":          "#7CB9C1",  # Light Blue-Green
        "border_focused":  "#00CED1",  # Dark Turquoise
        "card":            "#E0F7FA",  # Pale Cyan
        "modal":           "#B2EBF2",  # Light Cyan
        "button":          "#00CED1",  # Dark Turquoise
        "button_focused":  "#00B4B9",  # Deeper Turquoise
        "text":            "#194D54",  # Dark Teal
        "subtext":         "#5F9EA0",  # Cadet Blue
        "body":            "#E0F7FA",  # Pale Cyan
        "disabled":        "#B2EBF2",  # Light Cyan
        "active":          "#20B2AA",  # Light Sea Green
        "primary":         "#00CED1",  # Dark Turquoise
        "secondary":       "#4682B4",  # Steel Blue
        "tertiary":        "#FFA500",  # Orange
        "background":      "#F0F8FF",  # Alice Blue
        "foreground":      "#194D54",  # Dark Teal
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

        # Role colors
        "user":      "#556B2F",  # Dark Olive Green
        "assistant": "#2E8B57",  # Sea Green
        "system":    "#66CDAA",  # Medium Aquamarine
        "tool":      "#228B22",  # Forest Green

        # UI elements
        "border":          "#A0D6B4",  # Light Green
        "border_focused":  "#2E8B57",  # Sea Green
        "card":            "#F1F8E9",  # Pale Green
        "modal":           "#DCEDC8",  # Light Green
        "button":          "#2E8B57",  # Sea Green
        "button_focused":  "#227446",  # Darker Green
        "text":            "#1B5E20",  # Deep Green
        "subtext":         "#66CDAA",  # Medium Aquamarine
        "body":            "#F1F8E9",  # Pale Green
        "disabled":        "#C5E1A5",  # Light Yellow-Green
        "active":          "#00FF7F",  # Spring Green
        "primary":         "#2E8B57",  # Sea Green
        "secondary":       "#9ACD32",  # Yellow Green
        "tertiary":        "#DAA520",  # Goldenrod
        "background":      "#F8FFF0",  # Lightest Green
        "foreground":      "#1B5E20",  # Deep Green
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

        # Role colors
        "user":      "#FF8E71",  # Coral
        "assistant": "#FFA07A",  # Light Salmon
        "system":    "#FF6347",  # Tomato
        "tool":      "#CD5C5C",  # Indian Red

        # UI elements
        "border":          "#FFCCBC",  # Light Peach
        "border_focused":  "#FFA07A",  # Light Salmon
        "card":            "#FFF5F2",  # Pale Pink
        "modal":           "#FFE0B2",  # Light Orange
        "button":          "#FFA07A",  # Light Salmon
        "button_focused":  "#FF7043",  # Deep Orange
        "text":            "#5D4037",  # Deep Brown
        "subtext":         "#FF6347",  # Tomato
        "body":            "#FFF5F2",  # Pale Pink
        "disabled":        "#FFCCBC",  # Light Peach
        "active":          "#32CD32",  # Lime Green
        "primary":         "#FFA07A",  # Light Salmon
        "secondary":       "#FF69B4",  # Hot Pink
        "tertiary":        "#FFA500",  # Orange
        "background":      "#FFF9F5",  # Cream
        "foreground":      "#5D4037",  # Deep Brown
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

        # Role colors
        "user":      "#8EB2DE",  # Periwinkle
        "assistant": "#B0C4DE",  # Light Steel Blue
        "system":    "#2F4F4F",  # Dark Slate Gray
        "tool":      "#7CFC00",  # Lawn Green

        # UI elements
        "border":          "#4F5B66",  # Medium Gray-Blue
        "border_focused":  "#B0C4DE",  # Light Steel Blue
        "card":            "#1C2331",  # Dark Blue-Black
        "modal":           "#2C3E50",  # Dark Blue
        "button":          "#B0C4DE",  # Light Steel Blue
        "button_focused":  "#8EB2DE",  # Periwinkle
        "text":            "#E6E6FA",  # Lavender
        "subtext":         "#708090",  # Slate Gray
        "body":            "#1C2331",  # Dark Blue-Black
        "disabled":        "#4F5B66",  # Medium Gray-Blue
        "active":          "#00FA9A",  # Medium Spring Green
        "primary":         "#B0C4DE",  # Light Steel Blue
        "secondary":       "#4682B4",  # Steel Blue
        "tertiary":        "#DAA520",  # Goldenrod
        "background":      "#0F1620",  # Near Black
        "foreground":      "#E6E6FA",  # Lavender
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

        # Role colors
        "user":      "#F0B6FF",  # Soft Lavender
        "assistant": "#FFB6C1",  # Light Pink
        "system":    "#D8BFD8",  # Thistle
        "tool":      "#90EE90",  # Light Green

        # UI elements
        "border":          "#E6E6FA",  # Lavender
        "border_focused":  "#FFB6C1",  # Light Pink
        "card":            "#FFFFFF",  # White
        "modal":           "#FFF0F5",  # Lavender Blush
        "button":          "#FFB6C1",  # Light Pink
        "button_focused":  "#FFA0AB",  # Deeper Pink
        "text":            "#5D4D5D",  # Muted Eggplant
        "subtext":         "#D8BFD8",  # Thistle
        "body":            "#FFF5F9",  # Pale Pink
        "disabled":        "#E6E6FA",  # Lavender
        "active":          "#98FB98",  # Pale Green
        "primary":         "#FFB6C1",  # Light Pink
        "secondary":       "#AFEEEE",  # Pale Turquoise
        "tertiary":        "#FFE4B5",  # Moccasin
        "background":      "#FFFFFF",  # White
        "foreground":      "#5D4D5D",  # Muted Eggplant
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

        # Role colors
        "user":      "#F5AB35",  # Golden Amber
        "assistant": "#FFD700",  # Gold
        "system":    "#FFDAB9",  # Peach Puff
        "tool":      "#228B22",  # Forest Green

        # UI elements
        "border":          "#FFE0B2",  # Light Orange
        "border_focused":  "#FFD700",  # Gold
        "card":            "#FFF8E1",  # Light Yellow
        "modal":           "#FFF3CD",  # Pale Yellow
        "button":          "#FFD700",  # Gold
        "button_focused":  "#F9A825",  # Amber
        "text":            "#5D4037",  # Brown
        "subtext":         "#FFDAB9",  # Peach Puff
        "body":            "#FFF8E1",  # Light Yellow
        "disabled":        "#FFE0B2",  # Light Orange
        "active":          "#32CD32",  # Lime Green
        "primary":         "#FFD700",  # Gold
        "secondary":       "#FF8C00",  # Dark Orange
        "tertiary":        "#FFA500",  # Orange
        "background":      "#FFFDF5",  # Cream
        "foreground":      "#5D4037",  # Brown
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

        # Role colors
        "user":      "#FF7F50",  # Coral
        "assistant": "#FF6347",  # Tomato
        "system":    "#CD5C5C",  # Indian Red
        "tool":      "#FFA07A",  # Light Salmon

        # UI elements
        "border":          "#E57373",  # Lighter Red
        "border_focused":  "#FF6347",  # Tomato
        "card":            "#FFEBEE",  # Pale Red
        "modal":           "#FFCCBC",  # Peach
        "button":          "#FF6347",  # Tomato
        "button_focused":  "#E53935",  # Bright Red
        "text":            "#3E2723",  # Dark Brown
        "subtext":         "#CD5C5C",  # Indian Red
        "body":            "#FFEBEE",  # Pale Red
        "disabled":        "#FFCCBC",  # Peach
        "active":          "#FFA07A",  # Light Salmon
        "primary":         "#FF6347",  # Tomato
        "secondary":       "#FF4500",  # Orange Red
        "tertiary":        "#FF8C00",  # Dark Orange
        "background":      "#FFF5F5",  # Lightest Red
        "foreground":      "#3E2723",  # Dark Brown
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

        # Role colors
        "user":      "#66CDAA",  # Medium Aquamarine
        "assistant": "#98FB98",  # Pale Green
        "system":    "#AFEEEE",  # Pale Turquoise
        "tool":      "#2E8B57",  # Sea Green

        # UI elements
        "border":          "#B2DFDB",  # Light Teal
        "border_focused":  "#98FB98",  # Pale Green
        "card":            "#F1FFF8",  # Lightest Mint
        "modal":           "#E0F2F1",  # Pale Teal
        "button":          "#98FB98",  # Pale Green
        "button_focused":  "#66CDAA",  # Medium Aquamarine
        "text":            "#00695C",  # Deep Teal
        "subtext":         "#AFEEEE",  # Pale Turquoise
        "body":            "#F1FFF8",  # Lightest Mint
        "disabled":        "#B2DFDB",  # Light Teal
        "active":          "#20B2AA",  # Light Sea Green
        "primary":         "#98FB98",  # Pale Green
        "secondary":       "#66CDAA",  # Medium Aquamarine
        "tertiary":        "#ADFF2F",  # Green Yellow
        "background":      "#F0FFF0",  # Honeydew
        "foreground":      "#00695C",  # Deep Teal
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

        # Role colors
        "user":      "#A0522D",  # Sienna
        "assistant": "#8B4513",  # Saddle Brown
        "system":    "#BC8F8F",  # Rosy Brown
        "tool":      "#228B22",  # Forest Green

        # UI elements
        "border":          "#BCAAA4",  # Light Brown
        "border_focused":  "#8B4513",  # Saddle Brown
        "card":            "#F5F5DC",  # Beige
        "modal":           "#EFEBE9",  # Off-White
        "button":          "#8B4513",  # Saddle Brown
        "button_focused":  "#6D4C41",  # Deeper Brown
        "text":            "#3E2723",  # Very Dark Brown
        "subtext":         "#8D6E63",  # Medium Brown
        "body":            "#F5F5DC",  # Beige
        "disabled":        "#D7CCC8",  # Light Taupe
        "active":          "#32CD32",  # Lime Green
        "primary":         "#8B4513",  # Saddle Brown
        "secondary":       "#D2B48C",  # Tan
        "tertiary":        "#F4A460",  # Sandy Brown
        "background":      "#FFF8E1",  # Light Wheat
        "foreground":      "#3E2723",  # Very Dark Brown
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

        # Role colors
        "user":      "#DB7093",  # Pale Violet Red
        "assistant": "#FF69B4",  # Hot Pink
        "system":    "#FFB6C1",  # Light Pink
        "tool":      "#BA55D3",  # Medium Orchid

        # UI elements
        "border":          "#F8BBD0",  # Light Pink
        "border_focused":  "#FF69B4",  # Hot Pink
        "card":            "#FFF9FB",  # Lightest Pink
        "modal":           "#FCE4EC",  # Pale Pink
        "button":          "#FF69B4",  # Hot Pink
        "button_focused":  "#EC407A",  # Deeper Pink
        "text":            "#880E4F",  # Deep Magenta
        "subtext":         "#FFB6C1",  # Light Pink
        "body":            "#FFF9FB",  # Lightest Pink
        "disabled":        "#F8BBD0",  # Light Pink
        "active":          "#EE82EE",  # Violet
        "primary":         "#FF69B4",  # Hot Pink
        "secondary":       "#DB7093",  # Pale Violet Red
        "tertiary":        "#FFC0CB",  # Pink
        "background":      "#FFF9FB",  # Lightest Pink
        "foreground":      "#880E4F",  # Deep Magenta
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

        # Role colors
        "user":      "#1E90FF",  # Dodger Blue
        "assistant": "#87CEFA",  # Light Sky Blue
        "system":    "#87CEEB",  # Sky Blue
        "tool":      "#00CED1",  # Dark Turquoise

        # UI elements
        "border":          "#B3E5FC",  # Lighter Blue
        "border_focused":  "#87CEFA",  # Light Sky Blue
        "card":            "#F2FAFF",  # Lightest Blue
        "modal":           "#E1F5FE",  # Pale Blue
        "button":          "#87CEFA",  # Light Sky Blue
        "button_focused":  "#4FC3F7",  # Brighter Blue
        "text":            "#01579B",  # Deep Blue
        "subtext":         "#87CEEB",  # Sky Blue
        "body":            "#F2FAFF",  # Lightest Blue
        "disabled":        "#B3E5FC",  # Lighter Blue
        "active":          "#00FA9A",  # Medium Spring Green
        "primary":         "#87CEFA",  # Light Sky Blue
        "secondary":       "#4682B4",  # Steel Blue
        "tertiary":        "#DAA520",  # Goldenrod
        "background":      "#F8FCFF",  # White-Blue
        "foreground":      "#01579B",  # Deep Blue
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

        # Role colors
        "user":      "#1E90FF",  # Dodger Blue
        "assistant": "#4169E1",  # Royal Blue
        "system":    "#B0C4DE",  # Light Steel Blue
        "tool":      "#6A5ACD",  # Slate Blue

        # UI elements
        "border":          "#BBDEFB",  # Light Blue
        "border_focused":  "#4169E1",  # Royal Blue
        "card":            "#F1F5FF",  # Pale Blue
        "modal":           "#E3F2FD",  # Light Blue
        "button":          "#4169E1",  # Royal Blue
        "button_focused":  "#3151B5",  # Deeper Blue
        "text":            "#1A237E",  # Dark Blue
        "subtext":         "#B0C4DE",  # Light Steel Blue
        "body":            "#F1F5FF",  # Pale Blue
        "disabled":        "#BBDEFB",  # Light Blue
        "active":          "#00FF7F",  # Spring Green
        "primary":         "#4169E1",  # Royal Blue
        "secondary":       "#4682B4",  # Steel Blue
        "tertiary":        "#DAA520",  # Goldenrod
        "background":      "#F8FBFF",  # Near White Blue
        "foreground":      "#1A237E",  # Dark Blue
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

        # Role colors
        "user":      "#BA55D3",  # Medium Orchid
        "assistant": "#DA70D6",  # Orchid
        "system":    "#DDA0DD",  # Plum
        "tool":      "#C71585",  # Medium Violet Red

        # UI elements
        "border":          "#E1BEE7",  # Light Purple
        "border_focused":  "#DA70D6",  # Orchid
        "card":            "#FDF7FF",  # Lightest Purple
        "modal":           "#F3E5F5",  # Pale Purple
        "button":          "#DA70D6",  # Orchid
        "button_focused":  "#C054BE",  # Deeper Orchid
        "text":            "#4A148C",  # Deep Purple
        "subtext":         "#DDA0DD",  # Plum
        "body":            "#FDF7FF",  # Lightest Purple
        "disabled":        "#E1BEE7",  # Light Purple
        "active":          "#EE82EE",  # Violet
        "primary":         "#DA70D6",  # Orchid
        "secondary":       "#BA55D3",  # Medium Orchid
        "tertiary":        "#DDA0DD",  # Plum
        "background":      "#FFF9FF",  # Near White Purple
        "foreground":      "#4A148C",  # Deep Purple
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

        # Role colors
        "user":      "#D87093",  # Pale Violet Red
        "assistant": "#C71585",  # Medium Violet Red
        "system":    "#D8BFD8",  # Thistle
        "tool":      "#8A2BE2",  # Blue Violet

        # UI elements
        "border":          "#F8BBD0",  # Light Pink
        "border_focused":  "#C71585",  # Medium Violet Red
        "card":            "#FFF0F4",  # Lightest Pink
        "modal":           "#FCE4EC",  # Pale Pink
        "button":          "#C71585",  # Medium Violet Red
        "button_focused":  "#AD1457",  # Deeper Pink
        "text":            "#880E4F",  # Deep Pink
        "subtext":         "#D8BFD8",  # Thistle
        "body":            "#FFF0F4",  # Lightest Pink
        "disabled":        "#F8BBD0",  # Light Pink
        "active":          "#EE82EE",  # Violet
        "primary":         "#C71585",  # Medium Violet Red
        "secondary":       "#D87093",  # Pale Violet Red
        "tertiary":        "#FFC0CB",  # Pink
        "background":      "#FFF5F8",  # Near White Pink
        "foreground":      "#880E4F",  # Deep Pink
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

        # Role colors
        "user":      "#1E90FF",  # Dodger Blue
        "assistant": "#00BFFF",  # Deep Sky Blue
        "system":    "#AFEEEE",  # Pale Turquoise
        "tool":      "#20B2AA",  # Light Sea Green

        # UI elements
        "border":          "#B2EBF2",  # Light Cyan
        "border_focused":  "#00BFFF",  # Deep Sky Blue
        "card":            "#E8F8FF",  # Lightest Sky Blue
        "modal":           "#E1F5FE",  # Pale Blue
        "button":          "#00BFFF",  # Deep Sky Blue
        "button_focused":  "#0091EA",  # Deeper Sky Blue
        "text":            "#01579B",  # Deep Blue
        "subtext":         "#AFEEEE",  # Pale Turquoise
        "body":            "#E8F8FF",  # Lightest Sky Blue
        "disabled":        "#B2EBF2",  # Light Cyan
        "active":          "#3CB371",  # Medium Sea Green
        "primary":         "#00BFFF",  # Deep Sky Blue
        "secondary":       "#1E90FF",  # Dodger Blue
        "tertiary":        "#87CEFA",  # Light Sky Blue
        "background":      "#F0FAFF",  # Near White Blue
        "foreground":      "#01579B",  # Deep Blue
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

        # Role colors
        "user":      "#FFD700",  # Gold
        "assistant": "#FFFACD",  # Lemon Chiffon
        "system":    "#FAFAD2",  # Light Goldenrod Yellow
        "tool":      "#9ACD32",  # Yellow Green

        # UI elements
        "border":          "#FFF9C4",  # Light Yellow
        "border_focused":  "#FFFACD",  # Lemon Chiffon
        "card":            "#FFFCF0",  # Cream
        "modal":           "#FFFDE7",  # Pale Yellow
        "button":          "#FFFACD",  # Lemon Chiffon
        "button_focused":  "#FFE082",  # Deeper Yellow
        "text":            "#827717",  # Olive
        "subtext":         "#FAFAD2",  # Light Goldenrod Yellow
        "body":            "#FFFCF0",  # Cream
        "disabled":        "#FFF9C4",  # Light Yellow
        "active":          "#32CD32",  # Lime Green
        "primary":         "#FFFACD",  # Lemon Chiffon
        "secondary":       "#FFD700",  # Gold
        "tertiary":        "#F5DEB3",  # Wheat
        "background":      "#FFFEF7",  # Near White Yellow
        "foreground":      "#827717",  # Olive
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

        # Role colors
        "user":      "#778899",  # Light Slate Gray
        "assistant": "#708090",  # Slate Gray
        "system":    "#2F4F4F",  # Dark Slate Gray
        "tool":      "#4682B4",  # Steel Blue

        # UI elements
        "border":          "#CFD8DC",  # Light Blue-Gray
        "border_focused":  "#708090",  # Slate Gray
        "card":            "#F5F7FA",  # Pale Gray
        "modal":           "#ECEFF1",  # Light Blue-Gray
        "button":          "#708090",  # Slate Gray
        "button_focused":  "#546E7A",  # Deeper Slate
        "text":            "#263238",  # Dark Blue-Gray
        "subtext":         "#2F4F4F",  # Dark Slate Gray
        "body":            "#F5F7FA",  # Pale Gray
        "disabled":        "#CFD8DC",  # Light Blue-Gray
        "active":          "#20B2AA",  # Light Sea Green
        "primary":         "#708090",  # Slate Gray
        "secondary":       "#778899",  # Light Slate Gray
        "tertiary":        "#D3D3D3",  # Light Gray
        "background":      "#FAFBFD",  # Near White Gray
        "foreground":      "#263238",  # Dark Blue-Gray
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

        # Role colors
        "user":      "#8A2BE2",  # Blue Violet
        "assistant": "#9370DB",  # Medium Purple
        "system":    "#9400D3",  # Dark Violet
        "tool":      "#BA55D3",  # Medium Orchid

        # UI elements
        "border":          "#D1C4E9",  # Light Purple
        "border_focused":  "#9370DB",  # Medium Purple
        "card":            "#F5F0FA",  # Pale Purple
        "modal":           "#EDE7F6",  # Light Lavender
        "button":          "#9370DB",  # Medium Purple
        "button_focused":  "#7950D1",  # Deeper Purple
        "text":            "#4A148C",  # Deep Purple
        "subtext":         "#9400D3",  # Dark Violet
        "body":            "#F5F0FA",  # Pale Purple
        "disabled":        "#D1C4E9",  # Light Purple
        "active":          "#DA70D6",  # Orchid
        "primary":         "#9370DB",  # Medium Purple
        "secondary":       "#8A2BE2",  # Blue Violet
        "tertiary":        "#DDA0DD",  # Plum
        "background":      "#F8F5FC",  # Near White Purple
        "foreground":      "#4A148C",  # Deep Purple
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

        # Role colors
        "user":      "#FF1493",  # Deep Pink
        "assistant": "#FF69B4",  # Hot Pink
        "system":    "#FFB6C1",  # Light Pink
        "tool":      "#DB7093",  # Pale Violet Red

        # UI elements
        "border":          "#FFCDD2",  # Light Pink
        "border_focused":  "#FF69B4",  # Hot Pink
        "card":            "#FFF4F7",  # Palest Pink
        "modal":           "#FFEBEE",  # Pale Pink
        "button":          "#FF69B4",  # Hot Pink
        "button_focused":  "#F50057",  # Deeper Pink
        "text":            "#AD1457",  # Deep Pink
        "subtext":         "#FFB6C1",  # Light Pink
        "body":            "#FFF4F7",  # Palest Pink
        "disabled":        "#FFCDD2",  # Light Pink
        "active":          "#DB7093",  # Pale Violet Red
        "primary":         "#FF69B4",  # Hot Pink
        "secondary":       "#FF1493",  # Deep Pink
        "tertiary":        "#FFD1DC",  # Pale Pink
        "background":      "#FFF9FB",  # Near White Pink
        "foreground":      "#AD1457",  # Deep Pink
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

        # Role colors
        "user":      "#FF00FF",  # Neon Magenta
        "assistant": "#00FF00",  # Neon Green
        "system":    "#555555",  # Dark Gray
        "tool":      "#00FFFF",  # Cyan

        # UI elements
        "border":          "#444444",  # Medium Gray
        "border_focused":  "#00FF00",  # Neon Green
        "card":            "#111111",  # Near Black
        "modal":           "#222222",  # Dark Gray
        "button":          "#00FF00",  # Neon Green
        "button_focused":  "#00CC00",  # Darker Green
        "text":            "#DDDDDD",  # Light Gray
        "subtext":         "#555555",  # Dark Gray
        "body":            "#111111",  # Near Black
        "disabled":        "#444444",  # Medium Gray
        "active":          "#00FF7F",  # Spring Green
        "primary":         "#00FF00",  # Neon Green
        "secondary":       "#FF00FF",  # Neon Magenta
        "tertiary":        "#FFFF00",  # Neon Yellow
        "background":      "#000000",  # Black
        "foreground":      "#DDDDDD",  # Light Gray
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

        # Role colors
        "user":      "#FFFF00",  # Neon Yellow
        "assistant": "#FF00FF",  # Neon Magenta
        "system":    "#777777",  # Dim Gray
        "tool":      "#00FFFF",  # Bright Cyan

        # UI elements
        "border":          "#DDDDDD",  # Light Gray
        "border_focused":  "#FF00FF",  # Neon Magenta
        "card":            "#F0F0F0",  # Off-White
        "modal":           "#E0E0E0",  # Light Gray
        "button":          "#FF00FF",  # Neon Magenta
        "button_focused":  "#CC00CC",  # Darker Magenta
        "text":            "#111111",  # Near Black
        "subtext":         "#888888",  # Gray
        "body":            "#F0F0F0",  # Off-White
        "disabled":        "#DDDDDD",  # Light Gray
        "active":          "#00FF00",  # Bright Lime
        "primary":         "#FF00FF",  # Neon Magenta
        "secondary":       "#FFFF00",  # Neon Yellow
        "tertiary":        "#FFA500",  # Bright Orange
        "background":      "#FFFFFF",  # White
        "foreground":      "#111111",  # Near Black
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
