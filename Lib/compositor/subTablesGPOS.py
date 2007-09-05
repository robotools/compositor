from classDefinitionTables import ClassDef
from subTablesBase import BaseSubTable, BaseLookupRecord, Coverage,\
    BaseContextFormat1SubTable, BaseContextFormat2SubTable, BaseContextFormat3SubTable,\
    BaseChainingContextFormat1SubTable, BaseChainingContextFormat2SubTable, BaseChainingContextFormat3SubTable

try:
    reversed
except NameError:
    def reversed(iterable):
        iterable = list(iterable)
        iterable.reverse()
        return iterable

__all__ = [
        "GPOSLookupType1Format1", "GPOSLookupType1Format2",
        "GPOSLookupType2Format1", "GPOSLookupType2Format2",
        "GPOSLookupType3", "GPOSLookupType4", "GPOSLookupType5", "GPOSLookupType6",
        "GPOSLookupType7Format1", "GPOSLookupType7Format2", "GPOSLookupType7Format3",
        "GPOSLookupType8Format1", "GPOSLookupType8Format2", "GPOSLookupType8Format3",
        "GPOSLookupType9"
        ]


globalPositionSubTableSlots = ["PosFormat"]


class ValueRecord(object):

    """
    Deviation from spec:
    - XPlaDevice, YPlaDevice, XAdvDevice, YAdvDevice
      attributes are not implemented.
    """

    __slots__ = ["XPlacement", "YPlacement", "XAdvance", "YAdvance"]

    def __init__(self, valueRecord):
        self.XPlacement = 0
        self.YPlacement = 0
        self.XAdvance = 0
        self.YAdvance = 0
        if hasattr(valueRecord, "XPlacement"):
            self.XPlacement += valueRecord.XPlacement
        if hasattr(valueRecord, "YPlacement"):
            self.YPlacement += valueRecord.YPlacement
        if hasattr(valueRecord, "XAdvance"):
            self.XAdvance += valueRecord.XAdvance
        if hasattr(valueRecord, "YAdvance"):
            self.YAdvance += valueRecord.YAdvance


# -------------
# Lookup Type 1
# -------------


class GPOSLookupType1Format1(BaseSubTable):

    """
    Deviation from spec: None

    XXX need to handle ValueFormat?
    """

    __slots__ = ["Coverage", "ValueFormat", "Value"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType1Format1, self).__init__(subtable, lookup)
        self.PosFormat = 1
        self.Coverage = Coverage(subtable.Coverage)
        self.ValueFormat = subtable.ValueFormat
        self.Value = ValueRecord(subtable.Value)

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                performedPos = True
                currentRecord += self.Value
                processed.append(currentRecord)
                glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class GPOSLookupType1Format2(BaseSubTable):

    """
    Deviation from spec:
    - ValueCount attribute is not implemented.

    XXX need to handle ValueFormat?
    """

    __slots__ = ["Coverage", "ValueFormat", "Value"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType1Format2, self).__init__(subtable, lookup)
        self.PosFormat = 2
        self.Coverage = Coverage(subtable.Coverage)
        self.ValueFormat = subtable.ValueFormat
        self.Value = [ValueRecord(value) for value in subtable.Value]

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                performedPos = True
                valueIndex = self.Coverage.index(currentGlyph)
                value = self.Value[valueIndex]
                currentRecord += value
                processed.append(currentRecord)
                glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


# -------------
# Lookup Type 2
# -------------


class GPOSLookupType2Format1(BaseSubTable):

    """
    Deviation from spec:
    - PairSetCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "ValueFormat1", "ValueFormat2", "PairSet"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType2Format1, self).__init__(subtable, lookup)
        self.PosFormat = 1
        self.Coverage = Coverage(subtable.Coverage)
        self.ValueFormat1 = subtable.ValueFormat1
        self.ValueFormat2 = subtable.ValueFormat2
        self.PairSet = [PairSet(pairSet) for pairSet in subtable.PairSet]

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                nextRecord, nextRecordIndex = self._nextRecord(glyphRecords[1:])
                nextRecordIndex += 1
                if nextRecord is not None:
                    nextGlyph = nextRecord.glyphName
                    pairSetIndex = self.Coverage.index(currentGlyph)
                    pairSet = self.PairSet[pairSetIndex]
                    for pairValueRecord in pairSet.PairValueRecord:
                        if nextGlyph == pairValueRecord.SecondGlyph:
                            performedPos = True
                            if self.ValueFormat1:
                                currentRecord += pairValueRecord.Value1
                            if self.ValueFormat2:
                                nextRecord += pairValueRecord.Value2
                            if self.ValueFormat2:
                                processed.extend(glyphRecords[:nextRecordIndex+1])
                                glyphRecords = glyphRecords[nextRecordIndex+1:]
                            else:
                                processed.append(currentRecord)
                                glyphRecords = glyphRecords[1:]
                            break
        return processed, glyphRecords, performedPos


class PairSet(object):

    """
    Deviation from spec:
    - PairValueCount attribute is not implemented.
    """

    __slots__ = ["PairValueRecord"]

    def __init__(self, pairSet):
        self.PairValueRecord = [PairValueRecord(record) for record in pairSet.PairValueRecord]


class PairValueRecord(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["SecondGlyph", "Value1", "Value2"]

    def __init__(self, pairValueRecord):
        self.SecondGlyph = pairValueRecord.SecondGlyph
        self.Value1 = ValueRecord(pairValueRecord.Value1)
        self.Value2 = ValueRecord(pairValueRecord.Value2)


class GPOSLookupType2Format2(BaseSubTable):

    """
    Deviation from spec:
    - Class1Count attribute is not implemented.
    - Class2Count attribute is not implemented.
    """

    __slots__ = ["Coverage", "ValueFormat1", "ValueFormat2",
                "ClassDef1", "ClassDef2", "Class1Record"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType2Format2, self).__init__(subtable, lookup)
        self.Coverage = Coverage(subtable.Coverage)
        self.ValueFormat1 = subtable.ValueFormat1
        self.ValueFormat2 = subtable.ValueFormat2
        self.ClassDef1 = ClassDef(subtable.ClassDef1)
        self.ClassDef2 = ClassDef(subtable.ClassDef2)
        self.Class1Record = [Class1Record(record) for record in subtable.Class1Record]

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                nextRecord, nextRecordIndex = self._nextRecord(glyphRecords[1:])
                nextRecordIndex += 1
                if nextRecord is not None:
                    nextGlyph = nextRecord.glyphName
                    performedPos = True
                    class1Index = self.ClassDef1[currentGlyph]
                    class1Record = self.Class1Record[class1Index]
                    class2Index = self.ClassDef2[nextGlyph]
                    class2Record = class1Record.Class2Record[class2Index]
                    if self.ValueFormat1:
                        currentRecord += class2Record.Value1
                    if self.ValueFormat2:
                        nextRecord += class2Record.Value2
                    if self.ValueFormat2:
                        processed.extend(glyphRecords[:nextRecordIndex+1])
                        glyphRecords = glyphRecords[nextRecordIndex+1:]
                    else:
                        processed.append(currentRecord)
                        glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class Class1Record(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["Class2Record"]

    def __init__(self, class1Record):
        self.Class2Record = [Class2Record(record) for record in class1Record.Class2Record]


class Class2Record(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["Value1", "Value2"]

    def __init__(self, class2Record):
        self.Value1 = ValueRecord(class2Record.Value1)
        self.Value2 = ValueRecord(class2Record.Value2)


# -------------
# Lookup Type 3
# -------------


class GPOSLookupType3(BaseSubTable):

    """
    Deviation from spec:
    - EntryExitRecordCount attribute is not implemented.
    """

    __slots__ = ["Coverage", "EntryExitRecord"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType3, self).__init__(subtable, lookup)
        self.PosFormat = 1
        self.Coverage = Coverage(subtable.Coverage)
        self.EntryExitRecord = [EntryExitRecord(entryExitRecord) for entryExitRecord in subtable.EntryExitRecord]

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                nextRecord, nextRecordIndex = self._nextRecord(glyphRecords[1:])
                if nextRecord is not None:
                    nextGlyph = nextRecord.glyphName
                    if nextGlyph in self.Coverage:
                        performedPos = True
                        exitIndex = self.Coverage.index(currentGlyph)
                        exitAnchor = self.EntryExitRecord[exitIndex].ExitAnchor
                        entryIndex = self.Coverage.index(nextGlyph)
                        entryAnchor = self.EntryExitRecord[entryIndex].EntryAnchor
                        if exitAnchor is not None and entryAnchor is not None:
                            xOffset, yOffset = _calculateAnchorDifference(exitAnchor, entryAnchor)
                            nextRecord.xPlacement += xOffset
                            nextRecord.yPlacement += yOffset
                        processed.append(currentRecord)
                        glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class EntryExitRecord(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["EntryAnchor", "ExitAnchor"]

    def __init__(self, entryExitRecord):
        self.EntryAnchor = _createAnchor(entryExitRecord.EntryAnchor)
        self.ExitAnchor = _createAnchor(entryExitRecord.ExitAnchor)


# -------------
# Lookup Type 4
# -------------


class GPOSLookupType4(BaseSubTable):

    """
    Deviation from spec:
    - ClassCount attribute is not implemented.
    """

    __slots__ = ["MarkCoverage", "BaseCoverage", "MarkArray", "BaseArray"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType4, self).__init__(subtable, lookup)
        self.MarkCoverage = Coverage(subtable.MarkCoverage)
        self.BaseCoverage = Coverage(subtable.BaseCoverage)
        self.MarkArray = MarkArray(subtable.MarkArray)
        self.BaseArray = BaseArray(subtable.BaseArray)

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.MarkCoverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                previousRecord = None
                previousRecordIndex = 0
                gdef = self._lookup()._gdef
                # look back to find the most recent glyph that:
                # 1. is not covered by the lookup flag
                # 2. is not a mark glyph (as defined in the GDEF)
                while previousRecord is None:
                    for _previousRecord in reversed(processed):
                        previousRecordIndex -= 1
                        _previousGlyph = _previousRecord.glyphName
                        if not self._lookupFlagCoversGlyph(_previousGlyph):
                            if gdef is not None and gdef.GlyphClassDef[_previousGlyph] != 3:
                                previousRecord = _previousRecord
                                break
                    break
                if previousRecord is not None:
                    previousGlyph = previousRecord.glyphName
                    if previousGlyph in self.BaseCoverage:
                        performedPos = True
                        markCoverageIndex = self.MarkCoverage.index(currentGlyph)
                        markRecord = self.MarkArray.MarkRecord[markCoverageIndex]
                        markAnchor = markRecord.MarkAnchor
                        baseCoverageIndex = self.BaseCoverage.index(previousGlyph)
                        baseRecord = self.BaseArray.BaseRecord[baseCoverageIndex]
                        baseAnchor = baseRecord.BaseAnchor[markRecord.Class]
                        xOffset, yOffset = _calculateAnchorDifference(baseAnchor, markAnchor)
                        currentRecord.xPlacement += xOffset
                        currentRecord.yPlacement += yOffset
                        processed.append(currentRecord)
                        glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class MarkArray(object):

    """
    Deviation from spec:
    - MarkCount attribute is not implemented.
    """

    __slots__ = ["MarkRecord"]

    def __init__(self, markArray):
        self.MarkRecord = [MarkRecord(markRecord) for markRecord in markArray.MarkRecord]


class MarkRecord(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["Class", "MarkAnchor"]

    def __init__(self, markRecord):
        self.Class = markRecord.Class
        self.MarkAnchor = _createAnchor(markRecord.MarkAnchor)


class BaseArray(object):

    """
    Deviation from spec:
    - BaseCount attribute is not implemented.
    """

    __slots__ = ["BaseRecord"]

    def __init__(self, baseArray):
        self.BaseRecord = [BaseRecord(baseRecord) for baseRecord in baseArray.BaseRecord]


class BaseRecord(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["BaseAnchor"]

    def __init__(self, baseRecord):
        self.BaseAnchor = [_createAnchor(anchor) for anchor in baseRecord.BaseAnchor]


def _createAnchor(anchor):
    if anchor is None:
        return None
    if anchor.Format == 1:
        return AnchorFormat1(anchor)
    elif anchor.Format == 2:
        return AnchorFormat2(anchor)

def _calculateAnchorDifference(anchor1, anchor2):
    xDiff = anchor1.XCoordinate - anchor2.XCoordinate
    yDiff = anchor1.YCoordinate - anchor2.YCoordinate
    return xDiff, yDiff


class AnchorFormat1(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["AnchorFormat", "XCoordinate", "YCoordinate"]

    def __init__(self, anchor):
        self.AnchorFormat = 1
        self.XCoordinate = anchor.XCoordinate
        self.YCoordinate = anchor.YCoordinate


class AnchorFormat2(object):

    """
    Deviation from spec: None

    XXX this references a glyph contour point (as an index).
    not sure how that should be handled.
    """

    __slots__ = ["AnchorFormat", "XCoordinate", "YCoordinate", "AnchorPoint"]

    def __init__(self, anchor):
        self.AnchorFormat = 2
        self.XCoordinate = anchor.XCoordinate
        self.YCoordinate = anchor.YCoordinate
        self.AnchorPoint = anchor.AnchorPoint


# -------------
# Lookup Type 5
# -------------


class GPOSLookupType5(BaseSubTable):

    """
    Deviation from spec:
    - ClassCount attribute is not implemented.

    Note: This could process things in a buggy way.
    Not enough test cases are available to know for sure.
    """

    __slots__ = ["MarkCoverage", "LigatureCoverage", "MarkArray", "LigatureArray"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType5, self).__init__(subtable, lookup)
        self.MarkCoverage = Coverage(subtable.MarkCoverage)
        self.LigatureCoverage = Coverage(subtable.LigatureCoverage)
        self.MarkArray = MarkArray(subtable.MarkArray)
        self.LigatureArray = LigatureArray(subtable.LigatureArray)

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.MarkCoverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                previousRecord = None
                previousRecordIndex = 0
                gdef = self._lookup()._gdef
                # look back to find the most recent glyph that:
                # 1. is not covered by the lookup flag
                # 2. is not a mark glyph (as defined in the GDEF)
                while previousRecord is None:
                    for _previousRecord in reversed(processed):
                        previousRecordIndex -= 1
                        _previousGlyph = _previousRecord.glyphName
                        if not self._lookupFlagCoversGlyph(_previousGlyph):
                            if gdef is not None and gdef.GlyphClassDef[_previousGlyph] != 3:
                                previousRecord = _previousRecord
                                break
                    break
                if previousRecord is not None:
                    previousGlyph = previousRecord.glyphName
                    if previousGlyph in self.LigatureCoverage:
                        performedPos = True
                        markCoverageIndex = self.MarkCoverage.index(currentGlyph)
                        markRecord = self.MarkArray.MarkRecord[markCoverageIndex]
                        markAnchor = markRecord.MarkAnchor
                        ligatureCoverageIndex = self.LigatureCoverage.index(previousGlyph)
                        ligatureAttach = self.LigatureArray.LigatureAttach[ligatureCoverageIndex]
                        #componentIndex = previousRecord.ligatureComponents.index(???)
                        # XXX How is the component index determined?
                        componentIndex = 0 # XXX!?
                        componentRecord = ligatureAttach.ComponentRecord[componentIndex]
                        ligatureAnchor = componentRecord.LigatureAnchor[markRecord.Class]
                        xOffset, yOffset = _calculateAnchorDifference(ligatureAnchor, markAnchor)
                        currentRecord.xPlacement += xOffset
                        currentRecord.yPlacement += yOffset
                        processed.append(currentRecord)
                        glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class LigatureArray(object):

    """
    Deviation from spec:
    - LigatureCount attribute is not implemented.
    """

    __slots__ = ["LigatureAttach"]

    def __init__(self, ligatureArray):
        self.LigatureAttach = [LigatureAttach(ligatureAttach) for ligatureAttach in ligatureArray.LigatureAttach]


class LigatureAttach(object):

    """
    Deviation from spec:
    - ComponentCount attribute is not implemented.
    """

    __slots__ = ["ComponentRecord"]

    def __init__(self, ligatureAttach):
        self.ComponentRecord = [ComponentRecord(componentRecord) for componentRecord in ligatureAttach.ComponentRecord]


class ComponentRecord(object):

    """
    Deviation from spec: None

    XXX an anchor could be None. see the spec for more info.
    """

    __slots__ = ["LigatureAnchor"]

    def __init__(self, componentRecord):
        self.LigatureAnchor = [_createAnchor(anchor) for anchor in componentRecord.LigatureAnchor]


# -------------
# Lookup Type 6
# -------------


class GPOSLookupType6(BaseSubTable):

    """
    Deviation from spec:
    - ClassCount attribute is not implemented.

    Note: This could process things in a buggy way.
    Not enough test cases are available to know for sure.
    """

    __slots__ = ["Mark1Coverage", "Mark1Array", "Mark2Coverage", "Mark2Array"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType6, self).__init__(subtable, lookup)
        self.Mark1Coverage = Coverage(subtable.Mark1Coverage)
        self.Mark2Coverage = Coverage(subtable.Mark2Coverage)
        self.Mark1Array = MarkArray(subtable.Mark1Array)
        self.Mark2Array = Mark2Array(subtable.Mark2Array)

    def process(self, processed, glyphRecords, featureTag):
        performedPos = False
        currentRecord = glyphRecords[0]
        currentGlyph = currentRecord.glyphName
        if currentGlyph in self.Mark1Coverage:
            if not self._lookupFlagCoversGlyph(currentGlyph):
                previousRecord = None
                previousRecordIndex = 0
                gdef = self._lookup()._gdef
                while previousRecord is None:
                    for _previousRecord in reversed(processed):
                        previousRecordIndex -= 1
                        _previousGlyph = _previousRecord.glyphName
                        if not self._lookupFlagCoversGlyph(_previousGlyph):
                            previousRecord = _previousRecord
                            break
                    break
                if previousRecord is not None:
                    previousGlyph = previousRecord.glyphName
                    if previousGlyph in self.Mark2Coverage:
                        performedPos = True

                        mark1CoverageIndex = self.Mark1Coverage.index(currentGlyph)
                        mark1Record = self.Mark1Array.MarkRecord[mark1CoverageIndex]
                        mark1Anchor = mark1Record.MarkAnchor

                        mark2CoverageIndex = self.Mark2Coverage.index(previousGlyph)
                        mark2Record = self.Mark2Array.Mark2Record[mark2CoverageIndex]
                        mark2Anchor = mark2Record.Mark2Anchor[mark1Record.Class]
                        xOffset, yOffset = _calculateAnchorDifference(mark2Anchor, mark1Anchor)
                        currentRecord.xPlacement += xOffset
                        currentRecord.yPlacement += yOffset
                        processed.append(currentRecord)
                        glyphRecords = glyphRecords[1:]
        return processed, glyphRecords, performedPos


class Mark2Array(object):

    """
    Deviation from spec:
    - Mark2Count attribute is not implemented.
    """

    __slots__ = ["Mark2Record"]

    def __init__(self, mark2Array):
        self.Mark2Record = [Mark2Record(mark2Record) for mark2Record in mark2Array.Mark2Record]


class Mark2Record(object):

    """
    Deviation from spec: None
    """

    __slots__ = ["Mark2Anchor"]

    def __init__(self, mark2Record):
        self.Mark2Anchor = [_createAnchor(anchor) for anchor in mark2Record.Mark2Anchor]


# -------------
# Lookup Type 7
# -------------


class GPOSLookupType7Format1(BaseContextFormat1SubTable):

    """
    Deviation from spec:
    - PosRuleSetCount attribute is not implemented.

    A private attribute is implemented:
    _RuleSet - The value of PosRuleSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "PosRuleSet", "_RuleSet"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType7Format1, self).__init__(subtable, lookup)
        self.PosFormat = 1
        self.Coverage = Coverage(subtable.Coverage)
        self.PosRuleSet = [PosRuleSet(posRuleSet) for posRuleSet in subtable.PosRuleSet]
        self._RuleSet = self.PosRuleSet


class PosRuleSet(object):

    """
    Deviation from spec:
    - PosRuleCount attribute is not implemented.

    A private attribute is implemented:
    _Rule - The value of PosRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["PosRule", "_Rule"]

    def __init__(self, posRuleSet):
        self.PosRule = [PosRule(posRule) for posRule in posRuleSet.PosRule]
        self._Rule = self.PosRule


class PosRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of PosCount
    _ActionLookupRecord - The value of PosLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Input", "GlyphCount", "PosCount", "PosLookupRecord", "_ActionCount", "_ActionLookupRecord"]

    def __init__(self, posRule):
        self.Input = list(posRule.Input)
        self.GlyphCount = posRule.GlyphCount
        self.PosCount = posRule.PosCount
        self.PosLookupRecord = [PosLookupRecord(record) for record in posRule.PosLookupRecord]
        self._ActionCount = self.PosCount
        self._ActionLookupRecord = self.PosLookupRecord


class GPOSLookupType7Format2(BaseContextFormat2SubTable):

    """
    Deviation from spec:
    - PosClassRuleCnt attribute is not implemented.
    """

    __slots__ = ["Coverage", "ClassDef", "PosClassSet", "_ClassSet"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType7Format2, self).__init__(subtable, lookup)
        self.PosFormat = 2
        self.Coverage = Coverage(subtable.Coverage)
        self.ClassDef = ClassDef(subtable.ClassDef)
        self.PosClassSet = []
        for posClassSet in subtable.PosClassSet:
            if posClassSet is None:
                self.PosClassSet.append(None)
            else:
                self.PosClassSet.append(PosClassSet(posClassSet))
        self._ClassSet = self.PosClassSet


class PosClassSet(object):

    """
    Deviation from spec:
    - PosClassRuleCnt attribute is not implemented.
    """

    __slots__ = ["PosClassRule", "_ClassRule"]

    def __init__(self, posClassSet):
        self.PosClassRule = [PosClassRule(posClassRule) for posClassRule in posClassSet.PosClassRule]
        self._ClassRule = self.PosClassRule


class PosClassRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of PosCount
    _ActionLookupRecord - The value of PosLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Class", "GlyphCount", "PosCount", "PosLookupRecord", "_ActionCount", "_ActionLookupRecord"]

    def __init__(self, posClassRule):
        self.Class = list(posClassRule.Class)
        self.GlyphCount = posClassRule.GlyphCount
        self.PosCount = posClassRule.PosCount
        self.PosLookupRecord = [PosLookupRecord(record) for record in posClassRule.PosLookupRecord]
        self._ActionCount = self.PosCount
        self._ActionLookupRecord = self.PosLookupRecord


class GPOSLookupType7Format3(BaseContextFormat3SubTable):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of PosCount
    _ActionLookupRecord - The value of PosLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    def __init__(self, subtable, lookup):
        super(GPOSLookupType7Format3, self).__init__(subtable, lookup)
        self.PosFormat = 3
        self.Coverage = [Coverage(coverage) for coverage in subtable.Coverage]
        self.GlyphCount = subtable.GlyphCount
        self.PosCount = subtable.PosCount
        self.PosLookupRecord = [PosLookupRecord(record) for record in subtable.PosLookupRecord]
        self._ActionCount = self.PosCount
        self._ActionLookupRecord = self.PosLookupRecord


# -------------
# Lookup Type 8
# -------------


class GPOSLookupType8Format1(BaseChainingContextFormat1SubTable):

    """
    Deviation from spec:
    - ChainPosRuleSetCount attribute is not implemented.

    A private attribute is implemented:
    _ChainRuleSet - The value of ChainPosRuleSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "ChainPosRuleSet", "_ChainRuleSet"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType8Format1, self).__init__(subtable, lookup)
        self.PosFormat = 1
        self.Coverage = Coverage(subtable.Coverage)
        self.ChainPosRuleSet = [ChainPosRuleSet(chainPosRuleSet) for chainPosRuleSet in subtable.ChainPosRuleSet]
        self._ChainRuleSet = self.ChainPosRuleSet


class ChainPosRuleSet(object):

    """
    Deviation from spec:
    - ChainPosRuleCount attribute is not implemented.

    A private attribute is implemented:
    _ChainRule - The value of ChainPosRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["ChainPosRule", "_ChainRule"]

    def __init__(self, chainPosRuleSet):
        self.ChainPosRule = [ChainPosRule(chainPosRule) for chainPosRule in chainPosRuleSet.ChainPosRule]
        self._ChainRule = self.ChainPosRule


class ChainPosRule(object):

    """
    Deviation from spec: None

    Two private attributes are implemented:
    _ActionCount - The value of PosCount
    _ActionLookupRecord - The value of PosLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["BacktrackGlyphCount", "Backtrack", "InputGlyphCount", "Input",
                "LookAheadGlyphCount", "LookAhead",
                "PosCount", "PosLookupRecord",
                "_ActionCount", "_ActionLookupRecord"]

    def __init__(self, chainPosRule):
        self.BacktrackGlyphCount = chainPosRule.BacktrackGlyphCount
        self.Backtrack = list(chainPosRule.Backtrack)
        self.InputGlyphCount = chainPosRule.InputGlyphCount
        self.Input = list(chainPosRule.Input)
        self.LookAheadGlyphCount = chainPosRule.LookAheadGlyphCount
        self.LookAhead = list(chainPosRule.LookAhead)
        self.PosCount = chainPosRule.PosCount
        self.PosLookupRecord = [PosLookupRecord(record) for record in chainPosRule.PosLookupRecord]
        self._ActionCount = self.PosCount
        self._ActionLookupRecord = self.PosLookupRecord


class GPOSLookupType8Format2(BaseChainingContextFormat2SubTable):

    """
    Deviation from spec:
    -ChainPosClassSetCnt attribute is not implemented.

    A private attribute is implemented:
    _ChainClassSet - The value of ChainPosClassSet

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["Coverage", "BacktrackClassDef", "InputClassDef",
        "LookAheadClassDef", "ChainPosClassSet", "_ChainClassSet"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType8Format2, self).__init__(subtable, lookup)
        self.PosFormat = 2
        self.Coverage = Coverage(subtable.Coverage)
        self.BacktrackClassDef = ClassDef(subtable.BacktrackClassDef)
        self.InputClassDef = ClassDef(subtable.InputClassDef)
        self.LookAheadClassDef = ClassDef(subtable.LookAheadClassDef)
        self.ChainPosClassSet = []
        for chainPosClassSet in subtable.ChainPosClassSet:
            if chainPosClassSet is None:
                self.ChainPosClassSet.append(None)
            else:
                self.ChainPosClassSet.append(ChainPosClassSet(chainPosClassSet))
        self._ChainClassSet = self.ChainPosClassSet


class ChainPosClassSet(object):

    """
    Deviation from spec:
    -ChainPosClassRuleCnt attribute is not implemented.

    A private attribute is implemented:
    _ChainClassRule - The value of ChainPosClassRule

    The private attribute is needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["ChainPosClassRule", "_ChainClassRule"]

    def __init__(self, chainPosClassSet):
        self.ChainPosClassRule = [ChainPosClassRule(chainPosClassRule) for chainPosClassRule in chainPosClassSet.ChainPosClassRule]
        self._ChainClassRule = self.ChainPosClassRule


class ChainPosClassRule(object):

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
        "PosCount", "PosLookupRecord",
        "_ActionCount", "_ActionLookupRecord"]

    def __init__(self, chainPosClassRule):
        self.BacktrackGlyphCount = chainPosClassRule.BacktrackGlyphCount
        self.Backtrack = list(chainPosClassRule.Backtrack)
        self.InputGlyphCount = chainPosClassRule.InputGlyphCount
        self.Input = list(chainPosClassRule.Input)
        self.LookAheadGlyphCount = chainPosClassRule.LookAheadGlyphCount
        self.LookAhead = list(chainPosClassRule.LookAhead)
        self.PosCount = chainPosClassRule.PosCount
        self.PosLookupRecord = [PosLookupRecord(record) for record in chainPosClassRule.PosLookupRecord]
        self._ActionCount = self.PosCount
        self._ActionLookupRecord = self.PosLookupRecord


class GPOSLookupType8Format3(BaseChainingContextFormat3SubTable):

    """
    Deviation from spec:
    - PosCount and PosLookupRecord attributes are not implemented,
      In their place, two private attributes are implemented:
    _ActionCount - The value of PosCount
    _ActionLookupRecord - The value of PosLookupRecord

    The private attributes are needed because the contextual subtable processing
    is abstracted so that it can be shared between GSUB and GPOS.
    """

    __slots__ = ["BacktrackGlyphCount", "BacktrackCoverage", "InputGlyphCount", "InputCoverage"
                "LookaheadGlyphCount", "LookaheadCoverage",
                "_ActionCount", "_ActionLookupRecord"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType8Format3, self).__init__(subtable, lookup)
        self._ActionCount = subtable.PosCount
        self._ActionLookupRecord = [PosLookupRecord(record) for record in subtable.PosLookupRecord]


class PosLookupRecord(BaseLookupRecord): pass


# -------------
# Lookup Type 9
# -------------


class GPOSLookupType9(BaseSubTable):

    """
    Deviation from spec:
    - ExtensionOffset attribute is not implemented. In its place
      is the ExtSubTable attribute. That attribute references
      the subtable that should be used for processing.
    """

    __slots__ = ["ExtensionLookupType", "ExtSubTable"] + globalPositionSubTableSlots

    def __init__(self, subtable, lookup):
        super(GPOSLookupType9, self).__init__(subtable, lookup)
        self.ExtensionLookupType = subtable.ExtensionLookupType
        lookupType = self.ExtensionLookupType
        if lookupType == 1:
            cls = (GPOSLookupType1Format1, GPOSLookupType1Format2)[subtable.ExtSubTable.Format-1]
        elif lookupType == 2:
            cls = (GPOSLookupType2Format1, GPOSLookupType2Format2)[subtable.ExtSubTable.Format-1]
        elif lookupType == 3:
            cls = GPOSLookupType3
        elif lookupType == 4:
            cls = GPOSLookupType4
        elif lookupType == 5:
            cls = GPOSLookupType5
        elif lookupType == 6:
            cls = GPOSLookupType6
        elif lookupType == 7:
            cls = (GPOSLookupType7Format1, GPOSLookupType7Format2, GPOSLookupType7Format3)[subtable.ExtSubTable.Format-1]
        elif lookupType == 8:
            cls = (GPOSLookupType8Format1, GPOSLookupType8Format2, GPOSLookupType8Format3)[subtable.ExtSubTable.Format-1]
        elif lookupType == 9:
            cls = GPOSLookupType9
        self.ExtSubTable = cls(subtable.ExtSubTable, lookup)

    def process(self, processed, glyphRecords, featureTag):
        return self.ExtSubTable.process(processed, glyphRecords, featureTag)

