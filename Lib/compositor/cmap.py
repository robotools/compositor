"""
Utilities for handling the cmap table
and character mapping in general.
"""

def extractCMAP(ttFont):
    return ttFont["cmap"].getcmap(3, 1).cmap

def reverseCMAP(cmap):
    reversed = {}
    for value, name in cmap.items():
        if name not in reversed:
            reversed[name] = []
        reversed[name].append(value)
    return reversed
