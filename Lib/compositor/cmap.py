"""
Utilities for handling the cmap table
and character mapping in general.
"""

def extractCMAP(ttFont):
    cmap = {}
    cmapIDs = [(3, 10), (0, 3), (3, 1)]
    for i in range(len(cmapIDs)):
        if ttFont["cmap"].getcmap(*cmapIDs[i]):
            cmap = ttFont["cmap"].getcmap(*cmapIDs[i]).cmap
            break
    if not cmap:
        from compositor.error import CompositorError
        raise CompositorError("Found neither CMAP (3, 10), (0, 3), nor (3, 1) in font.")
    return cmap

def reverseCMAP(cmap):
    reversed = {}
    for value, name in cmap.items():
        if name not in reversed:
            reversed[name] = []
        reversed[name].append(value)
    return reversed
