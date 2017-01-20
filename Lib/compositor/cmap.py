"""
Utilities for handling the cmap table
and character mapping in general.
"""

def extractCMAP(ttFont):
    for platformID, encodingID in [(3, 10), (0, 3), (3, 1)]:
        cmapSubtable = ttFont["cmap"].getcmap(platformID, encodingID)
        if cmapSubtable is not None:
            return cmapSubtable.cmap
    from compositor.error import CompositorError
    raise CompositorError("Found neither CMAP (3, 10), (0, 3), nor (3, 1) in font.")

def reverseCMAP(cmap):
    reversed = {}
    for value, name in cmap.items():
        if name not in reversed:
            reversed[name] = []
        reversed[name].append(value)
    return reversed
