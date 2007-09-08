import unicodedata
from compositor.cmap import reverseCMAP
from compositor.caseConversionMaps import lowerToSingleUpper, upperToSingleLower, specialCasing, softDotted
from compositor.wordBreakProperties import wordBreakProperties

try:
    set
except NameError:
    from sets import Set as set

try:
    reversed
except NameError:
    def reversed(iterable):
        iterable = list(iterable)
        iterable.reverse()
        return iterable

# ---------------
# Case Conversion
# ---------------

def convertCase(case, glyphNames, cmap, reversedCMAP, language=None, fallbackGlyph=".notdef"):
    """
    Case Conversion Function

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
            madeChange = _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, reversedCMAP, language)
            if madeChange:
                continue
        # no specific language required
        madeChange = _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, reversedCMAP, None)
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

def _handleSpecialCasing(case, glyphs, index, uniValue, converted, cmap, reversedCMAP, language):
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
            ## Final_Sigma
            # Within the closest word boundaries 
            # containing C, there is a cased letter 
            # before C, and there is no cased letter 
            # after C.
            elif context == "Final_Sigma":
                glyphNames = [cmap.get(i, i) for i in glyphs]
                if isWordBreakAfter(glyphNames, index, reversedCMAP):
                    contextMatch = True
            ## Unknown
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

# -----------------------
# Word Boundary Detection
# -----------------------
# This implements the default word boundary algorithm explained here:
# http://www.unicode.org/reports/tr29/tr29-11.html#Default_Word_Boundaries

_notBreakBefore = set([
    # Do not break within CRLF
    (convertCodeToInt("240D"), convertCodeToInt("240A")),
    # Do not break between most letters.
    ("ALetter", "ALetter"),
    # Do not break across certain punctuation.
    ("ALetter", "MidLetter", "ALetter"),
    # Do not break within sequences of digits, or digits adjacent to letters.
    ("Numeric", "Numeric"),
    ("Numeric", "ALetter"),
    ("ALetter", "Numeric"),
    # Do not break within sequences, such as "3.2" or "3,456.789".
    ("Numeric", "MidNum", "Numeric"),
    # Do not break between Katakana.
    ("Katakana", "Katakana"),
    # Do not break from extenders.
    ("ALetter", "ExtendNumLet"),
    ("Numeric", "ExtendNumLet"),
    ("Katakana", "ExtendNumLet"),
    ("ExtendNumLet", "ExtendNumLet"),
])

def isWordBreakBefore(glyphNames, index, reversedCMAP):
    """
    Returns a boolean declaring if the position
    before index can be considered a word break.
    """
    # Start of line
    if index == 0:
        return True
    # get the unicode values and word break properties
    # for the previous two, current and next glyphs.
    unicodeValue = reversedCMAP.get(glyphNames[index], [None])[0]
    wordBreakProperty = wordBreakProperties.get(unicodeValue)
    backOneUnicodeValue = reversedCMAP.get(glyphNames[index - 1], [None])[0]
    backOneWordBreakProperty = wordBreakProperties.get(backOneUnicodeValue)
    if index > 1:
        backTwoUnicodeValue = reversedCMAP.get(glyphNames[index - 2], [None])[0]
        backTwoWordBreakProperty = wordBreakProperties.get(backTwoUnicodeValue)
    else:
        backTwoUnicodeValue = False
        backTwoWordBreakProperty = False
    if index < len(glyphNames) - 1:
        forwardOneUnicodeValue = reversedCMAP.get(glyphNames[index + 1], [None])[0]
        forwardOneWordBreakProperty = wordBreakProperties.get(forwardOneUnicodeValue)
    else:
        forwardOneUnicodeValue = None
        forwardOneWordBreakProperty = None
    # test the previous and current unicode values
    if (backOneUnicodeValue, unicodeValue) in _notBreakBefore:
        return False
    # test the previous and current word break properties
    if (backOneWordBreakProperty, wordBreakProperty) in _notBreakBefore:
        return False
    # test the previous, current and next word break properties
    if (backOneWordBreakProperty, wordBreakProperty, forwardOneWordBreakProperty) in _notBreakBefore:
        return False
    # test the previous, current and next word break properties
    if (backTwoWordBreakProperty, backOneWordBreakProperty, wordBreakProperty) in _notBreakBefore:
        return False
    # Otherwise, break everywhere (including around ideographs).
    return True

_notBreakAfter = set([
    # Do not break within CRLF
    (convertCodeToInt("240D"), convertCodeToInt("240A")),
    # Do not break between most letters.
    ("ALetter", "ALetter"),
    # Do not break across certain punctuation.
    ("ALetter", "MidLetter", "ALetter"),
    # Do not break within sequences of digits, or digits adjacent to letters.
    ("Numeric", "Numeric"),
    ("Numeric", "ALetter"),
    ("ALetter", "Numeric"),
    # Do not break within sequences, such as "3.2" or "3,456.789".
    ("Numeric", "MidNum", "Numeric"),
    # Do not break between Katakana.
    ("Katakana", "Katakana"),
    # Do not break from extenders.
    ("ExtendNumLet", "ALetter"),
    ("ExtendNumLet", "Numeric"),
    ("ExtendNumLet", "Katakana"),
])

def isWordBreakAfter(glyphNames, index, reversedCMAP):
    """
    Returns a boolean declaring if the position
    after index can be considered a word break.
    """
    # End of line
    if index == len(glyphNames) - 1:
        return True
    # get the unicode values and word break properties
    # for the previous, current and next two glyphs.
    unicodeValue = reversedCMAP.get(glyphNames[index], [None])[0]
    wordBreakProperty = wordBreakProperties.get(unicodeValue)
    forwardOneUnicodeValue = reversedCMAP.get(glyphNames[index + 1], [None])[0]
    forwardOneWordBreakProperty = wordBreakProperties.get(forwardOneUnicodeValue)
    if index > 0:
        backOneUnicodeValue = reversedCMAP.get(glyphNames[index - 1], [None])[0]
        backOneWordBreakProperty = wordBreakProperties.get(backOneUnicodeValue)
    else:
        backOneUnicodeValue = None
        backOneWordBreakProperty = None
    if index < len(glyphNames) - 2:
        forwardTwoUnicodeValue = reversedCMAP.get(glyphNames[index + 2], [None])[0]
        forwardTwoWordBreakProperty = wordBreakProperties.get(forwardTwoUnicodeValue)
    else:
        forwardTwoUnicodeValue = None
        forwardTwoWordBreakProperty = None
    # test the current and next unicode values
    if (unicodeValue, forwardOneUnicodeValue) in _notBreakAfter:
        return False
    # test the current and next word break properties
    if (wordBreakProperty, forwardOneWordBreakProperty) in _notBreakAfter:
        return False
    # test the previous, current and next word break properties
    if (backOneWordBreakProperty, wordBreakProperty, forwardOneWordBreakProperty) in _notBreakAfter:
        return False
    # test the current and next two word break properties
    if (wordBreakProperty, forwardOneWordBreakProperty, forwardTwoWordBreakProperty) in _notBreakAfter:
        return False
    # Otherwise, break everywhere (including around ideographs).
    return True

# -----
# Tests
# -----

# Case Conversion

def testCaseConversionSimple():
    """
    >>> cmap = {convertCodeToInt("0041") : "A",
    ...         convertCodeToInt("0061") : "a"
    ...         }
    >>> convertCase("upper", ["a", "a.alt"], cmap, reverseCMAP(cmap), None)
    ['A', 'a.alt']
    """

def testCaseConversionSimpleMissing():
    """
    >>> cmap = {convertCodeToInt("0061") : "a"}
    >>> convertCase("upper", ["a"], cmap, reverseCMAP(cmap), None)
    ['.notdef']
    """

def testCaseConversionLowerAfterI():
    """
    >>> cmap = {convertCodeToInt("0049") : "I",
    ...         convertCodeToInt("0069") : "i",
    ...         convertCodeToInt("0307") : "dotabove",
    ...         convertCodeToInt("0300") : "grave"
    ...         }
    >>> convertCase("lower", ["I", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i']
    """

def testCaseConversionUpperAfterSoftDotted():
    """
    >>> cmap = {convertCodeToInt("0049") : "I",
    ...         convertCodeToInt("0069") : "i",
    ...         convertCodeToInt("0307") : "dotabove",
    ...         convertCodeToInt("0300") : "grave"
    ...         }
    >>> convertCase("upper", ["i", "dotabove"], cmap, reverseCMAP(cmap), "LTH")
    ['I']
    >>> convertCase("upper", ["i", "grave", "dotabove"], cmap, reverseCMAP(cmap), "LTH")
    ['I', 'grave', 'dotabove']
    """

def testCaseConversionLowerMoreAbove():
    """
    >>> cmap = {convertCodeToInt("0049") : "I",
    ...         convertCodeToInt("0069") : "i",
    ...         convertCodeToInt("0307") : "dotabove",
    ...         convertCodeToInt("0300") : "grave"
    ...         }
    >>> convertCase("lower", ["I", "grave"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'dotabove', 'grave']
    >>> convertCase("lower", ["I", "I", "grave"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'i', 'dotabove', 'grave']
    >>> convertCase("lower", ["I", "I"], cmap, reverseCMAP(cmap), "LTH")
    ['i', 'i']
    """

def testCaseConversionLowerNotBeforeDot():
    """
    >>> cmap = {convertCodeToInt("0049") : "I",
    ...         convertCodeToInt("0069") : "i",
    ...         convertCodeToInt("0307") : "dotabove",
    ...         convertCodeToInt("0131") : "dotlessi",
    ...         convertCodeToInt("0327") : "cedilla"
    ...         }
    >>> convertCase("lower", ["I"], cmap, reverseCMAP(cmap), "TRK")
    ['dotlessi']
    >>> convertCase("lower", ["I", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i']
    >>> convertCase("lower", ["I", "cedilla", "dotabove"], cmap, reverseCMAP(cmap), "TRK")
    ['i', 'cedilla']
    """

def testCaseConversionFinalSigma():
    """
    >>> cmap = {convertCodeToInt("03A3") : "Sigma",
    ...         convertCodeToInt("03C3") : "sigma",
    ...         convertCodeToInt("03C2") : "finalsigma",
    ...         convertCodeToInt("0020") : "space",
    ...         }
    >>> convertCase("lower", ["Sigma", "Sigma"], cmap, reverseCMAP(cmap))
    ['sigma', 'finalsigma']
    >>> convertCase("lower", ["Sigma", "Sigma", "space"], cmap, reverseCMAP(cmap))
    ['sigma', 'finalsigma', 'space']
    """

# Word Boundaries

def testBreakBefore():
    """
    >>> cmap = {convertCodeToInt("0020") : "space",
    ...         convertCodeToInt("0041") : "A",
    ...         convertCodeToInt("002E") : "period",
    ...         convertCodeToInt("003A") : "colon",
    ...         convertCodeToInt("005F") : "underscore",
    ...         convertCodeToInt("0031") : "one",
    ...         convertCodeToInt("31F0") : "ku",
    ...         }
    >>> cmap = reverseCMAP(cmap)

    # Start of line
    >>> isWordBreakBefore(["A", "A"], 0, cmap)
    True

    # ALetter, ALetter
    >>> isWordBreakBefore(["space", "A", "A"], 1, cmap)
    True
    >>> isWordBreakBefore(["space", "A", "A"], 2, cmap)
    False

    # ALetter, MidLetter, ALetter
    >>> isWordBreakBefore(["A", "colon", "A"], 1, cmap)
    False
    >>> isWordBreakBefore(["A", "colon", "A"], 2, cmap)
    False
    >>> isWordBreakBefore(["A", "colon", "A", "colon", "A"], 1, cmap)
    False
    >>> isWordBreakBefore(["A", "colon", "A", "colon", "A"], 2, cmap)
    False
    >>> isWordBreakBefore(["A", "colon", "A", "colon", "A"], 3, cmap)
    False
    >>> isWordBreakBefore(["A", "colon", "A", "colon", "A"], 4, cmap)
    False

    # Numeric, Numeric
    >>> isWordBreakBefore(["space", "one", "one"], 1, cmap)
    True
    >>> isWordBreakBefore(["space", "one", "one"], 2, cmap)
    False

    # ALetter, Numeric
    >>> isWordBreakBefore(["space", "A", "one"], 1, cmap)
    True
    >>> isWordBreakBefore(["space", "A", "one"], 2, cmap)
    False

    # Numeric, ALetter
    >>> isWordBreakBefore(["space", "one", "A"], 1, cmap)
    True
    >>> isWordBreakBefore(["space", "one", "A"], 2, cmap)
    False

    # Numeric, MidNum, Numeric
    >>> isWordBreakBefore(["one", "period", "one"], 1, cmap)
    False
    >>> isWordBreakBefore(["one", "period", "one"], 2, cmap)
    False

    # Katakana, Katakana
    >>> isWordBreakBefore(["space", "ku", "ku"], 1, cmap)
    True
    >>> isWordBreakBefore(["space", "ku", "ku"], 2, cmap)
    False

    # ALetter, ExtendNumLet
    >>> isWordBreakBefore(["A", "underscore"], 1, cmap)
    False

    # Numeric, ExtendNumLet
    >>> isWordBreakBefore(["one", "underscore"], 1, cmap)
    False

    # Katakana, ExtendNumLet
    >>> isWordBreakBefore(["ku", "underscore"], 1, cmap)
    False

    # ExtendNumLet, ExtendNumLet
    >>> isWordBreakBefore(["underscore", "underscore"], 1, cmap)
    False
    """

def testBreakAfter():
    """
    >>> cmap = {convertCodeToInt("0020") : "space",
    ...         convertCodeToInt("0041") : "A",
    ...         convertCodeToInt("002E") : "period",
    ...         convertCodeToInt("003A") : "colon",
    ...         convertCodeToInt("005F") : "underscore",
    ...         convertCodeToInt("0031") : "one",
    ...         convertCodeToInt("31F0") : "ku",
    ...         }
    >>> cmap = reverseCMAP(cmap)

    # End of line
    >>> isWordBreakAfter(["A", "A"], 1, cmap)
    True

    # ALetter, ALetter
    >>> isWordBreakAfter(["A", "A", "space"], 0, cmap)
    False
    >>> isWordBreakAfter(["A", "A", "space"], 1, cmap)
    True

    # ALetter, MidLetter, ALetter
    >>> isWordBreakAfter(["A", "colon", "A"], 0, cmap)
    False
    >>> isWordBreakAfter(["A", "colon", "A"], 1, cmap)
    False
    >>> isWordBreakAfter(["A", "colon", "A", "colon", "A"], 0, cmap)
    False
    >>> isWordBreakAfter(["A", "colon", "A", "colon", "A"], 1, cmap)
    False
    >>> isWordBreakAfter(["A", "colon", "A", "colon", "A"], 2, cmap)
    False
    >>> isWordBreakAfter(["A", "colon", "A", "colon", "A"], 3, cmap)
    False

    # Numeric, Numeric
    >>> isWordBreakAfter(["one", "one", "space"], 0, cmap)
    False
    >>> isWordBreakAfter(["one", "one", "space"], 1, cmap)
    True

    # ALetter, Numeric
    >>> isWordBreakAfter(["A", "one", "space"], 0, cmap)
    False
    >>> isWordBreakAfter(["A", "one", "space"], 1, cmap)
    True

    # Numeric, ALetter
    >>> isWordBreakAfter(["one", "A", "space"], 0, cmap)
    False
    >>> isWordBreakAfter(["one", "A", "space"], 1, cmap)
    True

    # Numeric, MidNum, Numeric
    >>> isWordBreakAfter(["one", "period", "one"], 0, cmap)
    False
    >>> isWordBreakAfter(["one", "period", "one"], 1, cmap)
    False
    >>> isWordBreakAfter(["one", "period", "one", "period", "one"], 0, cmap)
    False
    >>> isWordBreakAfter(["one", "period", "one", "period", "one"], 1, cmap)
    False
    >>> isWordBreakAfter(["one", "period", "one", "period", "one"], 2, cmap)
    False
    >>> isWordBreakAfter(["one", "period", "one", "period", "one"], 3, cmap)
    False

    # Katakana, Katakana
    >>> isWordBreakAfter(["ku", "ku", "space"], 0, cmap)
    False
    >>> isWordBreakAfter(["ku", "ku", "space"], 1, cmap)
    True

    # ALetter, ExtendNumLet
    >>> isWordBreakAfter(["underscore", "A"], 0, cmap)
    False

    # Numeric, ExtendNumLet
    >>> isWordBreakAfter(["underscore", "one"], 0, cmap)
    False

    # Katakana, ExtendNumLet
    >>> isWordBreakAfter(["underscore", "ku"], 0, cmap)
    False
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
