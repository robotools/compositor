from random import choice
from classDefinitionTables import ClassDef
from glyphRecord import glyphNamesToGlyphRecords
from subTablesBase import BaseSubTable, BaseLookupRecord, Coverage,\
    BaseContextFormat1SubTable, BaseContextFormat2SubTable, BaseContextFormat3SubTable,\
    BaseChainingContextFormat1SubTable, BaseChainingContextFormat2SubTable, BaseChainingContextFormat3SubTable

try:
    set
except NameError:
    from sets import Set as set

try:
    sorted
except NameError:
    def sorted(iterable):
        if not isinstance(iterable, list):
            iterable = list(iterable)
        iterable.sort()
        return iterable


__all__ = [
        "GSUBLookupType1Format2", "GSUBLookupType2", "GSUBLookupType3", "GSUBLookupType4",
        "GSUBLookupType5Format1", "GSUBLookupType5Format2", "GSUBLookupType5Format3",
        "GSUBLookupType6Format1", "GSUBLookupType6Format2", "GSUBLookupType6Format3",
        "GSUBLookupType7", "GSUBLookupType8"
        ]


globalSubstitutionSubTableSlots = ["SubstFormat"]


# -------------
# Lookup Type 1
# -------------


class GSUBLookupType1Format2(BaseSubTable):

    """
    Deviation from spec:
    - fontTools interprets Lookup Type 1 formats 1 and 2
      into the same object structure. As such, only format 2
      is needed.
    - GlyphCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "Substitute"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType1Format2, self).__init__()
        self.SubstFormat = 2
        self.Substitute = []
        self.Coverage = None

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType1Format2, self).loadFromFontTools(subtable, lookup)
        # fontTools has a custom implementation of this
        # subtable type, so it needs to be converted
        coverage = []
        self.Substitute = []
        for glyphName, alternate in sorted(subtable.mapping.items()):
            coverage.append(glyphName)
            self.Substitute.append(alternate)
        self.Coverage = Coverage().loadFromFontTools(coverage)
        return self

    def process(self, processed, glyphRecords, featureTag):
        performedSub = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                performedSub = True
                index = self.Coverage.index(currentGlyph)
                substitute = self.Substitute[index]
                # special behavior for aalt
                if featureTag == "aalt":
                    if currentRecord._alternatesReference != currentGlyph:
                        currentRecord._alternatesReference = currentGlyph
                        currentRecord.alternates = []
                    currentRecord.alternates.append(substitute)
                # standard behavior
                else:
                    currentRecord.saveState(currentRecord.glyphName)
                    currentRecord.glyphName = substitute
                processed.append(currentRecord)
                glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedSub


# -------------
# Lookup Type 2
# -------------


class GSUBLookupType2(BaseSubTable):

    """
    Deviation from spec:
    - SequenceCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "Sequence"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType2, self).__init__()
        self.SubstFormat = 1
        self.Coverage = None
        self.Sequence = []

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType2, self).loadFromFontTools(subtable, lookup)
        self.Coverage = Coverage().loadFromFontTools(subtable.Coverage)
        self.Sequence = [Sequence().loadFromFontTools(sequence) for sequence in subtable.Sequence]
        return self

    def process(self, processed, glyphRecords, featureTag):
        performedSub = False
        currentRecord = glyphRecords[0]
        currentGlyph  = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                # XXX all glyph subsitituion states are destroyed here
                performedSub = True
                index = self.Coverage.index(currentGlyph)
                sequence = self.Sequence[index]
                substitute = sequence.Substitute
                substitute = glyphNamesToGlyphRecords(substitute)
                processed.extend(substitute)
                glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedSub


class Sequence(object):

    """
    Deviation from spec:
    - GlyphCount attribute is not implemented.
    """

    __slots__ = ["Substitute"]

    def __init__(self):
        self.Substitute = []

    def loadFromFontTools(self, sequence):
        self.Substitute = list(sequence.Substitute)
        return self


# -------------
# Lookup Type 3
# -------------


class GSUBLookupType3(BaseSubTable):

    """
    Deviation from spec:
    - AlternateSetCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "AlternateSet", "AlternateSetCount"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType3, self).__init__()
        self.SubstFormat = 1
        self.AlternateSet = []
        self.Coverage = None
        self.AlternateSetCount = 0

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType3, self).loadFromFontTools(subtable, lookup)
        # fontTools has a custom implementation of this
        # subtable type, so it needs to be converted
        coverage = []
        self.AlternateSet = []
        for glyphName, alternates in subtable.alternates.items():
            coverage.append(glyphName)
            alternateSet = AlternateSet().loadFromFontTools(alternates)
            self.AlternateSet.append(alternateSet)
        self.Coverage = Coverage().loadFromFontTools(coverage)
        self.AlternateSetCount = len(self.AlternateSet)
        return self

    def process(self, processed, glyphRecords, featureTag):
        performedSub = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                performedSub = True
                index = self.Coverage.index(currentGlyph)
                alternateSet = self.AlternateSet[index]
                alternates = alternateSet.Alternate
                # special behavior for rand
                if featureTag == "rand":
                    currentRecord.saveState(currentRecord.glyphName)
                    currentRecord.glyphName = choice(alternates)
                # standard behavior
                else:
                    if currentRecord._alternatesReference != currentGlyph:
                        currentRecord._alternatesReference = currentGlyph
                        currentRecord.alternates = []
                    currentRecord.alternates.extend(alternates)
                processed.append(currentRecord)
                glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedSub


class AlternateSet(object):

    """
    Deviation from spec:
    - GlyphCount attribute is not implemented.
    """

    __slots__ = ["Alternate"]

    def __init__(self):
        self.Alternate = []

    def loadFromFontTools(self, alternates):
        self.Alternate = list(alternates)
        return self


# -------------
# Lookup Type 4
# -------------


class GSUBLookupType4(BaseSubTable):

    """
    Deviation from spec:
    - LigSetCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "LigatureSet"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType4, self).__init__()
        self.SubstFormat = 1
        self.LigatureSet = []
        self.Coverage = None

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType4, self).loadFromFontTools(subtable, lookup)
        # fontTools has a custom implementation of this
        # subtable type, so it needs to be converted
        coverage = []
        self.LigatureSet = []
        for glyphName, ligature in subtable.ligatures.items():
            ligatureSet = LigatureSet().loadFromFontTools(ligature)
            self.LigatureSet.append(ligatureSet)
            coverage.append(glyphName)
        self.Coverage = Coverage().loadFromFontTools(coverage)
        return self

    def process(self, processed, glyphRecords, featureTag):
        performedSub = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        lookupFlag = self._lookup().LookupFlag
        if currentGlyph in self.Coverage:
            if not lookupFlag.coversGlyph(currentGlyph):
                while not performedSub:
                    coverageIndex = self.Coverage.index(currentGlyph)
                    ligatureSet = self.LigatureSet[coverageIndex]
                    for ligature in ligatureSet.Ligature:
                        component = ligature.Component
                        componentCount = ligature.CompCount
                        currentComponentIndex = 0
                        matchedRecordIndexes = set()
                        lastWasMatch = False
                        for index, glyphRecord in enumerate(glyphRecords[1:]):
                            glyphName = glyphRecord.glyphName
                            if not lookupFlag.coversGlyph(glyphName):
                                if not glyphName == component[currentComponentIndex]:
                                    lastWasMatch = False
                                    break
                                else:
                                    lastWasMatch = True
                                    matchedRecordIndexes.add(index)
                                    currentComponentIndex += 1
                                    if currentComponentIndex == componentCount - 1:
                                        break
                        if lastWasMatch and currentComponentIndex == componentCount - 1:
                            performedSub = True
                            currentRecord.saveState([currentGlyph] + ligature.Component)
                            currentRecord.glyphName = ligature.LigGlyph
                            currentRecord.ligatureComponents = [currentGlyph] + ligature.Component
                            processed.append(currentRecord)
                            glyphRecords = [record for index, record in enumerate(glyphRecords[1:]) if index not in matchedRecordIndexes]
                            break
                    break
        return processed, glyphRecords, performedSub


class LigatureSet(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["LigatureCount", "Ligature"]

    def __init__(self):
        self.Ligature = []
        self.LigatureCount = 0

    def loadFromFontTools(self, ligatures):
        self.Ligature = [Ligature().loadFromFontTools(ligature) for ligature in ligatures]
        self.LigatureCount = len(self.Ligature)
        return self


class Ligature(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["LigGlyph", "CompCount", "Component"]

    def __init__(self):
        self.CompCount = None
        self.LigGlyph = None
        self.Component = []

    def loadFromFontTools(self, ligature):
        self.CompCount = ligature.CompCount
        self.LigGlyph = ligature.LigGlyph
        self.Component = list(ligature.Component)
        return self


# -------------
# Lookup Type 5
# -------------


class GSUBLookupType5Format1(BaseContextFormat1SubTable):

    """
    Deviation from spec:
    - SubRuleSetCount attribute is not implemented.

    A private attribute is implemented:
    _RuleSet - The value of SubRuleSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "SubRuleSet", "_RuleSet"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType5Format1, self).__init__()
        self.SubstFormat = 1
        self.Coverage = None
        self.SubRuleSet = []
        self._RuleSet = self.SubRuleSet

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType5Format1, self).loadFromFontTools(subtable, lookup)
        self.Coverage = Coverage().loadFromFontTools(subtable.Coverage)
        self.SubRuleSet = [SubRuleSet().loadFromFontTools(subRuleSet) for subRuleSet in subtable.SubRuleSet]
        self._RuleSet = self.SubRuleSet
        return self


class SubRuleSet(object):

    """
    Deviation from spec:
    - SubRuleCount attribute is not implemented.

    A private attribute is implemented:
    _Rule - The value of SubRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["SubRule", "_Rule"]

    def __init__(self):
        self.SubRule = []
        self._Rule = self.SubRule

    def loadFromFontTools(self, subRuleSet):
        self.SubRule = [SubRule().loadFromFontTools(subRule) for subRule in subRuleSet.SubRule]
        self._Rule = self.SubRule
        return self


class SubRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Input", "GlyphCount", "SubstCount", "SubstLookupRecord", "_ActionCount", "_ActionLookupRecord"]

    def __init__(self):
        self.Input = []
        self.GlyphCount = 0
        self.SubstCount = 0
        self.SubstLookupRecord = []
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, subRule):
        self.Input = list(subRule.Input)
        self.GlyphCount = subRule.GlyphCount
        self.SubstCount = subRule.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in subRule.SubstLookupRecord]
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


class GSUBLookupType5Format2(BaseContextFormat2SubTable):

    """
    Deviation from spec:
    - SubClassRuleCnt attribute is not implemented.
    """

    __slots__ = ["Coverage", "ClassDef", "SubClassSet", "_ClassSet"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType5Format2, self).__init__()
        self.SubstFormat = 2
        self.Coverage = None
        self.ClassDef = None
        self.SubClassSet = []
        self._ClassSet = self.SubClassSet

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType5Format2, self).loadFromFontTools(subtable, lookup)
        self.Coverage = Coverage().loadFromFontTools(subtable.Coverage)
        self.ClassDef = ClassDef().loadFromFontTools(subtable.ClassDef)
        self.SubClassSet = []
        for subClassSet in subtable.SubClassSet:
            if subClassSet is None:
                self.SubClassSet.append(None)
            else:
                self.SubClassSet.append(SubClassSet().loadFromFontTools(subClassSet))
        self._ClassSet = self.SubClassSet
        return self


class SubClassSet(object):

    """
    Deviation from spec:
    - SubClassRuleCnt attribute is not implemented.
    """

    __slots__ = ["SubClassRule", "_ClassRule"]

    def __init__(self):
        self.SubClassRule = []
        self._ClassRule = self.SubClassRule

    def loadFromFontTools(self, subClassSet):
        self.SubClassRule = [SubClassRule().loadFromFontTools(subClassRule) for subClassRule in subClassSet.SubClassRule]
        self._ClassRule = self.SubClassRule
        return self


class SubClassRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Class", "GlyphCount", "SubstCount", "SubstLookupRecord", "_ActionCount", "_ActionLookupRecord"]

    def __init__(self):
        self.Class = []
        self.GlyphCount = 0
        self.SubstCount = 0
        self.SubstLookupRecord = []
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, subClassRule):
        self.Class = list(subClassRule.Class)
        self.GlyphCount = subClassRule.GlyphCount
        self.SubstCount = subClassRule.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in subClassRule.SubstLookupRecord]
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


class GSUBLookupType5Format3(BaseContextFormat3SubTable):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    def __init__(self):
        super(GSUBLookupType5Format3, self).__init__()
        self.SubstFormat = 3
        self.Coverage = []
        self.GlyphCount = 0
        self.SubstCount = 0
        self.SubstLookupRecord = []
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType5Format3, self).loadFromFontTools(subtable, lookup)
        self.Coverage = [Coverage().loadFromFontTools(coverage) for coverage in subtable.Coverage]
        self.GlyphCount = subtable.GlyphCount
        self.SubstCount = subtable.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in subtable.SubstLookupRecord]
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


# -------------
# Lookup Type 6
# -------------


class GSUBLookupType6Format1(BaseChainingContextFormat1SubTable):

    """
    Deviation from spec:
    - ChainSubRuleSetCount attribute is not implemented.

    A private attribute is implemented:
    _ChainRuleSet - The value of ChainSubRuleSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "ChainSubRuleSet", "_ChainRuleSet"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType6Format1, self).__init__()
        self.SubstFormat = 1
        self.Coverage = None
        self.ChainSubRuleSet = []
        self._ChainRuleSet = self.ChainSubRuleSet

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType6Format1, self).loadFromFontTools(subtable, lookup)
        self.Coverage = Coverage().loadFromFontTools(subtable.Coverage)
        self.ChainSubRuleSet = [ChainSubRuleSet().loadFromFontTools(chainSubRuleSet) for chainSubRuleSet in subtable.ChainSubRuleSet]
        self._ChainRuleSet = self.ChainSubRuleSet
        return self


class ChainSubRuleSet(object):

    """
    Deviation from spec:
    - ChainSubRuleCount attribute is not implemented.

    A private attribute is implemented:
    _ChainRule - The value of ChainSubRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["ChainSubRule", "_ChainRule"]

    def __init__(self):
        self.ChainSubRule = []
        self._ChainRule = self.ChainSubRule

    def loadFromFontTools(self, chainSubRuleSet):
        self.ChainSubRule = [ChainSubRule().loadFromFontTools(chainSubRule) for chainSubRule in chainSubRuleSet.ChainSubRule]
        self._ChainRule = self.ChainSubRule
        return self


class ChainSubRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["BacktrackGlyphCount", "Backtrack", "InputGlyphCount", "Input",
                "LookAheadGlyphCount", "LookAhead",
                "SubstCount", "SubstLookupRecord",
                "_ActionCount", "_ActionLookupRecord"]

    def __init__(self):
        self.BacktrackGlyphCount = 0
        self.Backtrack = []
        self.InputGlyphCount = 0
        self.Input = []
        self.LookAheadGlyphCount = 0
        self.LookAhead = []
        self.SubstCount = 0
        self.SubstLookupRecord = []
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, chainSubRule):
        self.BacktrackGlyphCount = chainSubRule.BacktrackGlyphCount
        self.Backtrack = list(chainSubRule.Backtrack)
        self.InputGlyphCount = chainSubRule.InputGlyphCount
        self.Input = list(chainSubRule.Input)
        self.LookAheadGlyphCount = chainSubRule.LookAheadGlyphCount
        self.LookAhead = list(chainSubRule.LookAhead)
        self.SubstCount = chainSubRule.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in chainSubRule.SubstLookupRecord]
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


class GSUBLookupType6Format2(BaseChainingContextFormat2SubTable):

    """
    Deviation from spec:
    -ChainSubClassSetCnt attribute is not implemented.

    A private attribute is implemented:
    _ChainClassSet - The value of ChainPosClassSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "BacktrackClassDef", "InputClassDef",
        "LookAheadClassDef", "ChainSubClassSet", "_ChainClassSet"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType6Format2, self).__init__()
        self.SubstFormat = 2
        self.Coverage = None
        self.BacktrackClassDef = None
        self.InputClassDef = None
        self.LookAheadClassDef = None
        self.ChainSubClassSet = []
        self._ChainClassSet = self.ChainSubClassSet

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType6Format2, self).loadFromFontTools(subtable, lookup)
        self.Coverage = Coverage().loadFromFontTools(subtable.Coverage)
        self.BacktrackClassDef = ClassDef().loadFromFontTools(subtable.BacktrackClassDef)
        self.InputClassDef = ClassDef().loadFromFontTools(subtable.InputClassDef)
        self.LookAheadClassDef = ClassDef().loadFromFontTools(subtable.LookAheadClassDef)
        self.ChainSubClassSet = []
        for chainSubClassSet in subtable.ChainSubClassSet:
            if chainSubClassSet is None:
                self.ChainSubClassSet.append(None)
            else:
                self.ChainSubClassSet.append(ChainSubClassSet().loadFromFontTools(chainSubClassSet))
        self._ChainClassSet = self.ChainSubClassSet
        return self


class ChainSubClassSet(object):

    """
    Deviation from spec:
    -ChainSubClassRuleCnt attribute is not implemented.

    A private attribute is implemented:
    _ChainClassRule - The value of ChainSubClassRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["ChainSubClassRule", "_ChainClassRule"]

    def __init__(self):
        self.ChainSubClassRule = None
        self._ChainClassRule = self.ChainSubClassRule

    def loadFromFontTools(self, chainSubClassSet):
        self.ChainSubClassRule = [ChainSubClassRule().loadFromFontTools(chainSubClassRule) for chainSubClassRule in chainSubClassSet.ChainSubClassRule]
        self._ChainClassRule = self.ChainSubClassRule
        return self


class ChainSubClassRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["BacktrackGlyphCount", "Backtrack",
        "InputGlyphCount", "Input",
        "LookAheadGlyphCount", "LookAhead",
        "SubstCount", "SubstLookupRecord",
        "_ActionCount", "_ActionLookupRecord"]

    def __init__(self):
        self.BacktrackGlyphCount = 0
        self.Backtrack = []
        self.InputGlyphCount = 0
        self.Input = []
        self.LookAheadGlyphCount = 0
        self.LookAhead = []
        self.SubstCount = 0
        self.SubstLookupRecord = []
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, chainSubClassRule):
        self.BacktrackGlyphCount = chainSubClassRule.BacktrackGlyphCount
        self.Backtrack = list(chainSubClassRule.Backtrack)
        self.InputGlyphCount = chainSubClassRule.InputGlyphCount
        self.Input = list(chainSubClassRule.Input)
        self.LookAheadGlyphCount = chainSubClassRule.LookAheadGlyphCount
        self.LookAhead = list(chainSubClassRule.LookAhead)
        self.SubstCount = chainSubClassRule.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in chainSubClassRule.SubstLookupRecord]
        self._ActionCount = self.SubstCount
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


class GSUBLookupType6Format3(BaseChainingContextFormat3SubTable):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of SubstCount
    _ActionLookupRecord - The value of SubstLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["BacktrackGlyphCount", "BacktrackCoverage", "InputGlyphCount", "InputCoverage"
                "LookaheadGlyphCount", "LookaheadCoverage",
                "SubstCount", "SubstLookupRecord",
                "_ActionCount", "_ActionLookupRecord"] + globalSubstitutionSubTableSlots

    def __init__(self):
        super(GSUBLookupType6Format3, self).__init__()
        self.SubstFormat = 3
        self.SubstCount = 0
        self._ActionCount = self.SubstCount
        self.SubstLookupRecord = []
        self._ActionLookupRecord = self.SubstLookupRecord

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType6Format3, self).loadFromFontTools(subtable, lookup)
        self.SubstCount = subtable.SubstCount
        self._ActionCount = self.SubstCount
        self.SubstLookupRecord = [SubstLookupRecord().loadFromFontTools(record) for record in subtable.SubstLookupRecord]
        self._ActionLookupRecord = self.SubstLookupRecord
        return self


class SubstLookupRecord(BaseLookupRecord): pass


# -------------
# Lookup Type 7
# -------------


class GSUBLookupType7(BaseSubTable):

    """
    Deviation from spec:
    - ExtensionOffset attribute is not implemented. In its place
      is the ExtSubTable attribute. That attribute references
      the subtable that should be used for processing.
    """

    __slots__ = ["ExtensionLookupType", "ExtSubTable"] + globalSubstitutionSubTableSlots

    def __init__(self):
        self.SubstFormat = 1
        self.ExtSubTable = None

    def loadFromFontTools(self, subtable, lookup):
        super(GSUBLookupType7, self).loadFromFontTools(subtable, lookup)
        self.ExtensionLookupType = subtable.ExtensionLookupType
        lookupType = self.ExtensionLookupType
        if lookupType == 1:
            cls = GSUBLookupType1Format2
        elif lookupType == 2:
            cls = GSUBLookupType2
        elif lookupType == 3:
            cls = GSUBLookupType3
        elif lookupType == 4:
            cls = GSUBLookupType4
        elif lookupType == 5:
            cls = (GSUBLookupType5Format1, GSUBLookupType5Format2, GSUBLookupType5Format3)[subtable.ExtSubTable.Format-1]
        elif lookupType == 6:
            cls = (GSUBLookupType6Format1, GSUBLookupType6Format2, GSUBLookupType6Format3)[subtable.ExtSubTable.Format-1]
        elif lookupType == 7:
            cls = GSUBLookupType7
        elif lookupType == 8:
            cls = GSUBLookupType8
        self.ExtSubTable = cls().loadFromFontTools(subtable.ExtSubTable, lookup)
        return self

    def process(self, processed, glyphRecords, featureTag):
        return self.ExtSubTable.process(processed, glyphRecords, featureTag)


# -------------
# Lookup Type 8
# -------------


class GSUBLookupType8(BaseSubTable): pass

