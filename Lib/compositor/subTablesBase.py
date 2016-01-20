from __future__ import print_function
import weakref

# ------------
# Base Classes
# ------------


class BaseSubTable(object):

    """
    This object implents the base level subtable behavior
    for GSUB and GPOS subtables. It establishes one private
    attribute, _lookup, which is a weak reference to the
    lookup that contains the subtable.
    """

    __slots__ = ["_lookup"]

    def __init__(self):
        self._lookup = None

    def loadFromFontTools(self, subtable, lookup):
        self._lookup = weakref.ref(lookup)
        return self

    def process(self, processed, glyphRecords, featureTag):
        if self._lookup is not None and hasattr(self._lookup(), "LookupType"):
            lookupType = self._lookup().LookupType
        else:
            lookupType = "Unknown"
        if hasattr(self, "SubstFormat"):
            format = str(self.SubstFormat)
        elif hasattr(self, "PosFormat"):
            format = str(self.PosFormat)
        else:
            format = "Unknown"
        className = self.__class__.__name__
        print("[Compositor] %s skipping Lookup Type %s Format %s" % (className, lookupType, format))
        return processed, glyphRecords, False

    def _lookupFlagCoversGlyph(self, glyphName):
        return self._lookup().LookupFlag.coversGlyph(glyphName)

    def _nextRecord(self, glyphRecords):
        nextRecord = None
        nextRecordIndex = 0
        while nextRecord is None:
            for _nextRecord in glyphRecords:
                _nextGlyph = _nextRecord.glyphName
                if not self._lookupFlagCoversGlyph(_nextGlyph):
                    nextRecord = _nextRecord
                    break
                nextRecordIndex += 1
            break
        return nextRecord, nextRecordIndex


class BaseContextSubTable(BaseSubTable):

    __slots__ = []

    def _processMatch(self, rule, processed, glyphRecords, inputGlyphCount, matchedIndexes, featureTag):
            performedAction = False
            if not rule._ActionCount:
                performedAction = True
                processed.extend(glyphRecords[:inputGlyphCount])
                glyphRecords = glyphRecords[inputGlyphCount:]
            else:
                eligibleRecords = glyphRecords[:inputGlyphCount]
                ineligibleRecords = glyphRecords[inputGlyphCount:]
                for record in rule._ActionLookupRecord:
                    sequenceIndex = record.SequenceIndex
                    matchIndex = matchedIndexes[sequenceIndex]

                    backRecords = eligibleRecords[:matchIndex]
                    inputRecords = eligibleRecords[matchIndex:]

                    lookupListIndex = record.LookupListIndex
                    lookup = self._lookup()._lookupList().Lookup[lookupListIndex]

                    for subtable in lookup.SubTable:
                        backRecords, inputRecords, performedAction = subtable.process(backRecords, inputRecords, featureTag)
                        if performedAction:
                            break
                    if performedAction:
                        eligibleRecords = backRecords + inputRecords
                processed.extend(eligibleRecords)
                glyphRecords = ineligibleRecords
            return processed, glyphRecords, performedAction


class BaseChainingContextSubTable(BaseContextSubTable):

    __slots__ = []

    def _testContext(self, testSource, testAgainst, matchCount, additionObjects=None):
        # this procedure is common across all formats
        # with the exception of evaluating if a particular
        # glyph matches a position in the context.
        # to handle this, the comparison is evaluated
        # by a _evaluateContextItem method in each
        # subclass. the speed penalty for this is negligible.
        # the aditionalObjects arg will be ignored by
        # all formats except format 2 which needs a ClassDef
        # to perform the comparison.
        completeRun = []
        matchedIndexes = []
        matched = 0
        while matched < matchCount:
            for recordIndex, glyphRecord in enumerate(testSource):
                completeRun.append(glyphRecord)
                glyphName = glyphRecord.glyphName
                if not self._lookupFlagCoversGlyph(glyphName):
                    if not self._evaluateContextItem(glyphName, testAgainst[matched], additionObjects):
                        break
                    matched += 1
                    matchedIndexes.append(recordIndex)
                    if matched == matchCount:
                        break
            break
        return matched == matchCount, completeRun, matchedIndexes


class BaseContextFormat1SubTable(BaseContextSubTable):

    __slots__ = []

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                coverageIndex = self.Coverage.index(currentGlyph)
                ruleSet = self._RuleSet[coverageIndex]
                for rule in ruleSet._Rule:
                    matchedIndexes = [0]
                    currentGlyphIndex = 1
                    for input in rule.Input:
                        glyphRecord, relativeIndex = self._nextRecord(glyphRecords[currentGlyphIndex:])
                        currentGlyphIndex += relativeIndex
                        if glyphRecord is not None:
                            glyphName = glyphRecord.glyphName
                            if glyphName != input:
                                break
                            else:
                                matchedIndexes.append(currentGlyphIndex)
                            currentGlyphIndex += 1
                    if len(matchedIndexes) == rule.GlyphCount:
                        inputGlyphCount = matchedIndexes[-1] + 1
                        processed, glyphRecords, performedAction = self._processMatch(rule, processed, glyphRecords, inputGlyphCount, matchedIndexes, featureTag)
                        if performedAction:
                            break
        return processed, glyphRecords, performedAction


class BaseContextFormat2SubTable(BaseContextSubTable):

    __slots__ = []

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                classIndex = self.ClassDef[currentGlyph]
                classSet = self._ClassSet[classIndex]
                if classSet is not None:
                    matchedIndexes = [0]
                    currentGlyphIndex = 1
                    for classRule in classSet._ClassRule:
                        for inputClass in classRule.Class:
                            glyphRecord, relativeIndex = self._nextRecord(glyphRecords[currentGlyphIndex:])
                            currentGlyphIndex += relativeIndex
                            if glyphRecord is not None:
                                glyphName = glyphRecord.glyphName
                                glyphClass = self.ClassDef[glyphName]
                                if glyphClass != inputClass:
                                    break
                                else:
                                    matchedIndexes.append(currentGlyphIndex)
                                currentGlyphIndex += 1
                        if len(matchedIndexes) == classRule.GlyphCount:
                            inputGlyphCount = matchedIndexes[-1] + 1
                            processed, glyphRecords, performedAction = self._processMatch(classRule, processed, glyphRecords, inputGlyphCount, matchedIndexes, featureTag)
        return processed, glyphRecords, performedAction


class BaseContextFormat3SubTable(BaseContextSubTable):

    __slots__ = []

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        matchedIndexes = []
        currentGlyphIndex = 0
        for coverage in self.Coverage:
            glyphRecord, relativeIndex = self._nextRecord(glyphRecords[currentGlyphIndex:])
            currentGlyphIndex += relativeIndex
            currentGlyph = glyphRecord.glyphName
            if currentGlyph not in coverage:
                break
            matchedIndexes.append(currentGlyphIndex)
            currentGlyphIndex += 1
        if len(matchedIndexes) == self.GlyphCount:
            inputGlyphCount = matchedIndexes[-1] + 1
            processed, glyphRecords, performedAction = self._processMatch(self, processed, glyphRecords, inputGlyphCount, matchedIndexes, featureTag)
        return processed, glyphRecords, performedAction


class BaseChainingContextFormat1SubTable(BaseChainingContextSubTable):

    __slots__ = []

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            for chainRuleSet in self._ChainRuleSet:
                for chainRule in chainRuleSet._ChainRule:
                    # backtrack testing
                    backtrackCount = chainRule.BacktrackGlyphCount
                    if not backtrackCount:
                        backtrackMatch = True
                    else:
                        backtrackMatch, backtrack, backtrackMatchIndexes = self._testContext(reversed(processed), chainRule.Backtrack, backtrackCount)
                    if not backtrackMatch:
                        continue
                    # input testing
                    inputCount = chainRule.InputGlyphCount
                    if not inputCount:
                        inputMatch = True
                    else:
                        inputMatch, input, inputMatchIndexes = self._testContext(glyphRecords[1:], chainRule.Input, inputCount-1)
                    if not inputMatch:
                        continue
                    input = [currentRecord] + input
                    inputMatchIndexes = [0] + [i + 1 for i in inputMatchIndexes]
                    # look ahead testing
                    lookAheadCount = chainRule.LookAheadGlyphCount
                    if not lookAheadCount:
                        lookAheadMatch = True
                    else:
                        lookAheadMatch, lookAhead, lookAheadMatchIndexes = self._testContext(glyphRecords[len(input):], chainRule.LookAhead, lookAheadCount)
                    if not lookAheadMatch:
                        continue
                    # match. process.
                    if backtrackMatch and inputMatch and lookAheadMatch:
                        processed, glyphRecords, performedAction = self._processMatch(chainRule, processed, glyphRecords, len(input), inputMatchIndexes, featureTag)
                        if performedAction:
                            # break the chainRule loop
                            break

                if performedAction:
                    # break the chainRuleSet loop
                    break
        return processed, glyphRecords, performedAction

    def _evaluateContextItem(self, glyphName, contextTest, additionalObject):
        return glyphName == contextTest


class BaseChainingContextFormat2SubTable(BaseChainingContextSubTable):

    __slots__ = []

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                classIndex = self.InputClassDef[currentGlyph]
                chainClassSet = self._ChainClassSet[classIndex]
                if chainClassSet is not None:
                    for chainClassRule in chainClassSet._ChainClassRule:
                        # backtrack testing
                        backtrackCount = chainClassRule.BacktrackGlyphCount
                        if not backtrackCount:
                            backtrackMatch = True
                        else:
                            backtrackMatch, backtrack, backtrackMatchIndexes = self._testContext(reversed(processed), chainClassRule.Backtrack, backtrackCount, self.BacktrackClassDef)
                        if not backtrackMatch:
                            continue
                        # input testing
                        inputCount = chainClassRule.InputGlyphCount
                        if not inputCount:
                            inputMatch = True
                        else:
                            inputMatch, input, inputMatchIndexes = self._testContext(glyphRecords[1:], chainClassRule.Input, inputCount-1, self.InputClassDef)
                        if not inputMatch:
                            continue
                        input = [currentRecord] + input
                        inputMatchIndexes = [0] + [i + 1 for i in inputMatchIndexes]
                        # look ahead testing
                        lookAheadCount = chainClassRule.LookAheadGlyphCount
                        if not lookAheadCount:
                            lookAheadMatch = True
                        else:
                            lookAheadMatch, lookAhead, lookAheadMatchIndexes = self._testContext(glyphRecords[len(input):], chainClassRule.LookAhead, lookAheadCount, self.LookAheadClassDef)
                        if not lookAheadMatch:
                            continue
                        # match. process.
                        if backtrackMatch and inputMatch and lookAheadMatch:
                            processed, glyphRecords, performedAction = self._processMatch(chainClassRule, processed, glyphRecords, len(input), inputMatchIndexes, featureTag)
                            if performedAction:
                                break
        return processed, glyphRecords, performedAction

    def _evaluateContextItem(self, glyphName, contextTest, additionalObject):
        classDef = additionalObject
        classIndex = classDef[glyphName]
        return classIndex == contextTest


class BaseChainingContextFormat3SubTable(BaseChainingContextSubTable):

    """
    This object implements chaining contextual format 3.
    It is shared across GSUB and GPOS contextual subtables.
    """

    __slots__ = ["BacktrackGlyphCount", "BacktrackCoverage", "InputGlyphCount",
                "InputCoverage", "LookAheadGlyphCount", "LookAheadCoverage"]

    def __init__(self):
        super(BaseChainingContextFormat3SubTable, self).__init__()
        self.BacktrackGlyphCount = 0
        self.BacktrackCoverage = []
        self.InputGlyphCount = 0
        self.InputCoverage = []
        self.LookAheadGlyphCount = 0
        self.LookAheadCoverage = []

    def loadFromFontTools(self, subtable, lookup):
        super(BaseChainingContextFormat3SubTable, self).loadFromFontTools(subtable, lookup)
        self.BacktrackGlyphCount = subtable.BacktrackGlyphCount
        self.BacktrackCoverage = [Coverage().loadFromFontTools(coverage) for coverage in subtable.BacktrackCoverage]
        self.InputGlyphCount = subtable.InputGlyphCount
        self.InputCoverage = [Coverage().loadFromFontTools(coverage) for coverage in subtable.InputCoverage]
        self.LookAheadGlyphCount = subtable.LookAheadGlyphCount
        self.LookAheadCoverage = [Coverage().loadFromFontTools(coverage) for coverage in subtable.LookAheadCoverage]
        return self

    def process(self, processed, glyphRecords, featureTag):
        performedAction = False
        while 1:
            # backtrack testing
            backtrackCount = self.BacktrackGlyphCount
            if not backtrackCount:
                backtrackMatch = True
            else:
                backtrackMatch, backtrack, backtrackMatchIndexes = self._testContext(reversed(processed), self.BacktrackCoverage, backtrackCount)
            if not backtrackMatch:
                break
            # input testing
            inputCount = self.InputGlyphCount
            if not inputCount:
                inputMatch = True
            else:
                inputMatch, input, inputMatchIndexes = self._testContext(glyphRecords, self.InputCoverage, inputCount)
            if not inputMatch:
                break
            # look ahead testing
            lookAheadCount = self.LookAheadGlyphCount
            if not lookAheadCount:
                lookAheadMatch = True
            else:
                lookAheadMatch, lookAhead, lookAheadMatchIndexes = self._testContext(glyphRecords[len(input):], self.LookAheadCoverage, lookAheadCount)
            if not lookAheadMatch:
                break
            # match. process.
            if backtrackMatch and inputMatch and lookAheadMatch:
                processed, glyphRecords, performedAction = self._processMatch(self, processed, glyphRecords, len(input), inputMatchIndexes, featureTag)
            # break the while
            break
        return processed, glyphRecords, performedAction

    def _evaluateContextItem(self, glyphName, contextTest, additionalObject):
        return glyphName in contextTest


class BaseLookupRecord(object):

    """
    This object implements the functionality of both
    GSUB SubstLookupRecord and GPOS PosLookupRecord.
    """

    __slots__ = ["SequenceIndex", "LookupListIndex"]

    def __init__(self):
        self.SequenceIndex = None
        self.LookupListIndex = None

    def loadFromFontTools(self, record):
        self.SequenceIndex = record.SequenceIndex
        self.LookupListIndex = record.LookupListIndex
        return self


# --------
# Coverage
# --------


class Coverage(object):

    """
    fontTools abstracts CoverageFormat1 and
    CoverageFormat2 into a common Coverage
    object. The same is done here. Consequently
    the structure of this object does not closely
    follow the specification. Instead, the basic
    functionality is implemented through standard
    dict methods.

    To determine if a glyph is in the coverage:
        >>> "x" in coverage
        True

    To get the index for a particular glyph:
        >>> coverage.index("x")
        330
    """

    __slots__ = ["_glyphs"]


    def __init__(self, coverage=None):
        if coverage is not None:
            coverage = list(coverage)
        self._glyphs = coverage

    def loadFromFontTools(self, coverage):
        # the data coming in could be a fontTools
        # Coverage object or a list of glyph names
        if not isinstance(coverage, list):
            coverage = coverage.glyphs
        self._glyphs = list(coverage)
        return self

    def __contains__(self, glyphName):
        return glyphName in self._glyphs

    def index(self, glyphName):
        return self._glyphs.index(glyphName)

    def _get_Glyphs(self):
        return list(self._glyphs)

    Glyphs = property(_get_Glyphs, doc="This is for reference only. Not for use in processing.")
