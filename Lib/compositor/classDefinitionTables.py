class ClassDef(object):

    """
    Deviation from spec:
    - StartGlyph attribute is not implemented.
    - GlyphCount attribute is not implemented.
    - ClassValueArray attribute is not implemented.

    The structure of this object does not closely
    follow the specification. Instead, the basic
    functionality is implemented through standard
    dict methods.

    To determine if a glyph is in the class:
        >>> "x" in aClass
        True

    To get the class value of a particular glyph:
        >>> aClass["x"]
        330
    """

    __slots__ = ["_map", "ClassFormat"]

    def __init__(self):
        self.ClassFormat = None
        self._map = None

    def loadFromFontTools(self, classDef):
        self.ClassFormat = classDef.Format
        self._map = dict(classDef.classDefs)
        return self

    def __getitem__(self, glyphName):
        return self._map.get(glyphName, 0)

    def _get_Glyphs(self):
        return self._map

    Glyphs = property(_get_Glyphs, doc="This is for reference only. Not for use in processing.")


class GlyphClassDef(ClassDef):

    """
    This is a subclass of ClassDefFormat1.

    Retrieving the class for a glyph from this
    object will always return a value. If the
    glyph is not in the class definitions,
    zero will be returned.
    """


class MarkAttachClassDef(ClassDef):

    """
    This is a subclass of ClassDefFormat1.

    Retrieving the class for a glyph from this
    object will always return a value. If the
    glyph is not in the class definitions,
    zero will be returned.
    """
