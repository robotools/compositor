class GlyphRecord(object):

    """
    GlyphRecord object.

    This is the object type which will be contained in the list
    returned by font.process("A String").

    This object should NOT be constructed outside of a
    Compositor context.

    This object contains the following attributes:
    - glyphName
      The glyph name.
    - xPlacement
    - yPlacement
    - xAdvance
    - yAdvance
      The numerical values that control the placement
      and advance of the glyph. For more information
      on these, check the ValueRecord specification
      here (scroll way down the page):
      http://www.microsoft.com/typography/otspec/gpos.htm
    - alternates
      This is a list containing alternates for the glyph
      referenced by this glyph record. During processing
      by the tables in the engine, this list of will be
      mutated and obliterated n number of times based on
      the features and lookups being processed. There is no
      guarantee that the alternates listed here will
      reference the final glyph contained in the record.
      Therefore, this validation is up to the caller.
      Also, the internal processing will populate this
      list with glyph names.
      Note: You do not need to worry about any of the
      validation or population issues discussed here
      if you are using the Font object. That
      object handles all of the necessary cleanup in
      the process method.
    - ligatureComponents
      This is a list of glyph names that are the
      components of a ligature.

    This object contains three methods for making educated
    guesses about Unicode values. This is necessary when
    word breaks are determined.
    - saveState
      This method saves the glyph name provided, which
      can either be a glyph name or a list of glyph names
      in the case of lgatures. This will add the glyph name
      to the record's substitution history. This should be
      done before a substitution is made.
    - getSide1GlyphNameWithUnicodeValue
    - getSide2GlyphNameWithUnicodeValue
      These two methods find the most recent glyph name
      for each side that has a Unicode value. When called,
      they work backwards through the glyph names saved with
      the saveState method until a glyph name with a Unicode
      value is found.
    """

    __slots__ = ["glyph", "glyphName", "xPlacement", "yPlacement",
                "xAdvance", "yAdvance", "advanceWidth", "advanceHeight",
                "alternates", "_alternatesReference",
                "_ligatureComponents", "_ligatureComponentsReference",
                "_substitutionHistory"]

    def __init__(self, glyphName):
        self.glyph = None
        self.glyphName = glyphName
        self.xPlacement = 0
        self.yPlacement = 0
        self.xAdvance = 0
        self.yAdvance = 0
        self.advanceWidth = 0
        self.advanceHeight = 0
        self.alternates = []
        self._alternatesReference = None
        self._ligatureComponents = []
        self._substitutionHistory = []

    def __repr__(self):
        name = str(self.glyphName)
        xP = str(self.xPlacement)
        yP = str(self.yPlacement)
        xA = str(self.xAdvance)
        yA = str(self.yAdvance)
        s = "<GlyphRecord: Name: %s XPlacement: %s YPlacement: %s XAdvance: %s YAdvance: %s>" % (name, xP, yP, xA, yA)
        return s

    def __add__(self, valueRecord):
        self.xPlacement += valueRecord.XPlacement
        self.yPlacement += valueRecord.YPlacement
        self.xAdvance += valueRecord.XAdvance
        self.yAdvance += valueRecord.YAdvance
        return self

    def _get_ligatureComponents(self):
        return list(self._ligatureComponents)

    def _set_ligatureComponents(self, components):
        self._ligatureComponents = list(components)

    ligatureComponents = property(_get_ligatureComponents, _set_ligatureComponents)

    def saveState(self, glyphName):
        if isinstance(glyphName, list):
            glyphName = list(glyphName)
        self._substitutionHistory.append(glyphName)

    def getSide1GlyphNameWithUnicodeValue(self, reversedCMAP):
        if self.glyphName in reversedCMAP:
            return self.glyphName
        for glyphName in reversed(self._substitutionHistory):
            if isinstance(glyphName, list):
                glyphName = glyphName[0]
            if glyphName in reversedCMAP:
                return glyphName
        return None

    def getSide2GlyphNameWithUnicodeValue(self, reversedCMAP):
        if self.glyphName in reversedCMAP:
            return self.glyphName
        for glyphName in reversed(self._substitutionHistory):
            if isinstance(glyphName, list):
                glyphName = glyphName[-1]
            if glyphName in reversedCMAP:
                return glyphName
        return None


def glyphNamesToGlyphRecords(glyphList):
    """
    >>> glyphList = ["a", "b"]
    >>> glyphNamesToGlyphRecords(glyphList)
    [<GlyphRecord: Name: a XPlacement: 0 YPlacement: 0 XAdvance: 0 YAdvance: 0>, <GlyphRecord: Name: b XPlacement: 0 YPlacement: 0 XAdvance: 0 YAdvance: 0>]
    """
    return [GlyphRecord(glyphName) for glyphName in glyphList]

def glyphRecordsToTuples(glyphRecords):
    """
    >>> vr = GlyphRecord("foo")
    >>> vr.xPlacement = 1
    >>> vr.yPlacement = 2
    >>> vr.xAdvance = 3
    >>> vr.yAdvance = 4
    >>> glyphRecordsToTuples([vr])
    [('foo', 1, 2, 3, 4)]
    """
    tuples = []
    for record in glyphRecords:
        xP = record.xPlacement
        yP = record.yPlacement
        xA = record.xAdvance
        yA = record.yAdvance
        gN = record.glyphName
        tuples.append((gN, xP, yP, xA, yA))
    return tuples

def glyphRecordsToGlyphNames(glyphRecords):
    """
    >>> glyphList = ["a", "b"]
    >>> glyphRecords = glyphNamesToGlyphRecords(glyphList)
    >>> glyphRecordsToGlyphNames(glyphRecords)
    ['a', 'b']
    """
    return [record.glyphName for record in glyphRecords]

def _testMath():
    """
    >>> from subTablesGPOS import ValueRecord
    >>> vr = ValueRecord()
    >>> vr.XPlacement = 1
    >>> vr.YPlacement = 2
    >>> vr.XAdvance = 3
    >>> vr.YAdvance = 4
    >>> gr = GlyphRecord("foo")
    >>> gr.xPlacement = 1
    >>> gr.yPlacement = 2
    >>> gr.xAdvance = 3
    >>> gr.yAdvance = 4
    >>> gr + vr
    <GlyphRecord: Name: foo XPlacement: 2 YPlacement: 4 XAdvance: 6 YAdvance: 8>
    """

def _testUnicodeGuessing():
    """
    >>> cmap = {
    ... "a" : 97,
    ... "b" : 98,
    ... }
    >>> r = GlyphRecord("a")
    >>> r.saveState("a")
    >>> r.glyphName = "a.alt1"
    >>> r.saveState("a.alt1")
    >>> r.glyphName = "a.alt2"
    >>> r.getSide1GlyphNameWithUnicodeValue(cmap)
    'a'
    >>> r.glyphName = "b"
    >>> r.getSide1GlyphNameWithUnicodeValue(cmap)
    'b'
    >>> r = GlyphRecord("a")
    >>> r.saveState(["a", "b"])
    >>> r.glyphName = "a_b"
    >>> r.getSide1GlyphNameWithUnicodeValue(cmap)
    'a'
    >>> r.getSide2GlyphNameWithUnicodeValue(cmap)
    'b'
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
