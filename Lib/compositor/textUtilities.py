import unicodedata
from layoutEngine.cmap import reverseCMAP
from layoutEngine.caseConversionMaps import lowerToSingleUpper, upperToSingleLower, specialCasing, softDotted

try:
    reversed
except NameError:
    def reversed(iterable):
        iterable = list(iterable)
        iterable.reverse()
        return iterable

def convertCase(case, glyphNames, cmap, reversedCMAP, language=None, fallbackGlyph=".notdef"):
    """
    Case Connversion Function

    This function converts a list of glyph names to their
    upper or lowercase forms following the Unicode locale
    specific case conversion rules.

    Arguments:
    - case
      The case to convert to. Valid values are "upper" and "lower".
    - glyphNames
      A list of glyph names.
    - cmap
      The CMAP for the font formatted as a dictionary.
    - reversedCMAP
      Reversed version of cmap.
    - language
      The language tag being processed. May be None.
    - fallbackGlyph
      The glyph name that should be used when the converted
      glyph does not exist in the font.
    """
    # before anything else happens, the glyph names
    # have to be converted to unicode values. if no
    # unicode value is available, the glyph name is used.
    glyphs = []
    for glyphName in glyphNames:
        uniValue = reversedCMAP.get(glyphName)
        if uniValue is None:
            glyphs.append(glyphName)
        else:
            glyphs.append(uniValue[0])
    converted = []
    for index, uniValue in enumerate(glyphs):
        # glyph name indicating that there is no available unicode
        if isinstance(uniValue, basestring):
            converted.append(uniValue)
            continue
        ## special casing
        # specific language
        if language is not None:
            madeChange = _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, language)
            if madeChange:
                continue
        # no specific language required
        madeChange = _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, None)
        if madeChange:
            continue
        ## single casing
        if case == "upper":
            d = lowerToSingleUpper
        else:
            d = upperToSingleLower
        if uniValue in d:
            converted.append(d[uniValue])
            continue
        ## fallback
        converted.append(uniValue)
    # convert back to glyph names
    glyphNames = []
    for uniValue in converted:
        if isinstance(uniValue, basestring):
            glyphNames.append(uniValue)
            continue
        glyphNames.append(cmap.get(uniValue, fallbackGlyph))
    return glyphNames

def convertCodeToInt(code):
    if not code:
        return None
    if " " in code:
        return tuple([convertCodeToInt(i) for i in code.split(" ")])
    return int(code, 16)

def _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, language):
    """
    Handle a language specific lookup.
    Returns a boolean indicating if a change was made.
    """
    if language not in specialCasing:
        return False
    languageMap = specialCasing[language]
    if uniValue in languageMap:
        contextMatch = True
        context = languageMap[uniValue]["context"]
        if context:
            contextMatch = False
            ## After_I
            # The last preceding base character was
            # an uppercase I, and there is no inter-
            # vening combining character class 230.
            if context == "After_I":
                previous = None
                for otherUniValue in reversed(glyphs[:index]):
                    previous = otherUniValue
                    if isinstance(otherUniValue, basestring):
                        break
                    combining = unicodedata.combining(unichr(otherUniValue))
                    if combining == 230:
                        previous = None
                        break
                    if combining == 0:
                        break
                if previous == convertCodeToInt("0049"):
                    contextMatch = True
            elif context == "Not_After_I":
                # not referenced in SpecialCasing
                raise NotImplementedError
            ## After_Soft_Dotted
            # The last preceding character with a
            # combining class of zero before C was
            # Soft_Dotted, and there is no interven-
            # ing combining character class 230
            elif context == "After_Soft_Dotted":
                previous = None
                for otherUniValue in reversed(glyphs[:index]):
                    previous = otherUniValue
                    if isinstance(otherUniValue, basestring):
                        break
                    combining = unicodedata.combining(unichr(otherUniValue))
                    if combining == 230:
                        previous = None
                        break
                    if combining == 0:
                        break
                if previous in softDotted:
                    contextMatch = True
            elif context == "Not_After_Soft_Dotted":
                # not referenced in SpecialCasing
                raise NotImplementedError
            ## More_Above
            # C is followed by one or more charac-
            # ters of combining class 230 (ABOVE)
            # in the combining character sequence.
            elif context == "More_Above":
                next = None
                for otherUniValue in glyphs[index+1:]:
                    next = otherUniValue
                    if isinstance(otherUniValue, basestring):
                        break
                    combining = unicodedata.combining(unichr(otherUniValue))
                    if combining == 230:
                        contextMatch = True
                        break
                    else:
                        break
            elif context == "Not_More_Above":
                # not referenced in SpecialCasing
                raise NotImplementedError
            ## Before_Dot
            # C is followed by U+0307 combining
            # dot above. Any sequence of charac- 
            # ters with a combining class that is nei- 
            # ther 0 nor 230 may intervene between 
            # the current character and the com- 
            # bining dot above.
            elif context == "Before_Dot":
                # not referenced in SpecialCasing
                raise NotImplementedError
            elif context == "Not_Before_Dot":
                next = None
                contextMatch = True
                for otherUniValue in glyphs[index+1:]:
                    if isinstance(otherUniValue, basestring):
                        break
                    if otherUniValue == convertCodeToInt("0307"):
                        contextMatch = False
                        break
                    else:
                        combining = unicodedata.combining(unichr(otherUniValue))
                        if combining == 0 or combining == 230:
                            break
            else:
                raise NotImplementedError(context)
        if contextMatch:
            conversion = languageMap[uniValue][case]
            # if the conversion is None, it means that the character should be removed.
            if conversion is None:
                return True
            # apply the conversion to the list of converted characters.
            if not isinstance(conversion, tuple):
                conversion = [conversion]
            for code in conversion:
                converted.append(code)
            return True
    return False

def _testSimple():
    """
    >>> cmap = {convertCodeToInt("0041") : "A", convertCodeToInt("0061") : "a"}
    >>> convertCase("upper", ["a", "a.alt"], cmap, reverseCMAP(cmap), None)
    ['A', 'a.alt']
    """

def _testSimpleMissing():
    """
    >>> cmap = {convertCodeToInt("0061") : "a"}
    >>> convertCase("upper", ["a"], cmap, reverseCMAP(cmap), None)
    ['.notdef']
    """

def _testLowerAfterI():
    """
    >>> cmap = {convertCodeToInt("0049") : "I", convertCodeToInt("0069") : "i", convertCodeToInt("0307") : "dotabove", convertCodeToInt("0300") : "grave"}
    >>> convertCase("lower", ["I", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i']
    """

def _testUpperAfterSoftDotted():
    """
    >>> cmap = {convertCodeToInt("0049") : "I", convertCodeToInt("0069") : "i", convertCodeToInt("0307") : "dotabove", convertCodeToInt("0300") : "grave"}
    >>> convertCase("upper", ["i", "dotabove"], cmap, reverseCMAP(cmap), "LTH")
    ['I']
    >>> convertCase("upper", ["i", "grave", "dotabove"], cmap, reverseCMAP(cmap), "LTH")
    ['I', 'grave', 'dotabove']
    """

def _testLowerMoreAbove():
    """
    >>> cmap = {convertCodeToInt("0049") : "I", convertCodeToInt("0069") : "i", convertCodeToInt("0307") : "dotabove", convertCodeToInt("0300") : "grave"}
    >>> convertCase("lower", ["I", "grave"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'dotabove', 'grave']
    >>> convertCase("lower", ["I", "I", "grave"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'i', 'dotabove', 'grave']
    >>> convertCase("lower", ["I", "I"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'i']
    """

def _testLowerNotBeforeDot():
    """
    >>> cmap = {convertCodeToInt("0049") : "I", convertCodeToInt("0069") : "i", convertCodeToInt("0307") : "dotabove", convertCodeToInt("0131") : "dotlessi", convertCodeToInt("0327") : "cedilla"}
    >>> convertCase("lower", ["I"], cmap, reverseCMAP(cmap), "TRK")
    ['dotlessi']
    >>> convertCase("lower", ["I", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i']
    >>> convertCase("lower", ["I", "cedilla", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i', 'cedilla']
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
