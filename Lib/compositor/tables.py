"""
GSUB, GPOS and GDEF table objects.
"""

import unicodedata
from compositor.cmap import reverseCMAP
from compositor.scriptList import ScriptList
from compositor.featureList import FeatureList
from compositor.lookupList import GSUBLookupList, GPOSLookupList
from compositor.subTablesBase import Coverage
from compositor.classDefinitionTables import MarkAttachClassDef, GlyphClassDef
from compositor.textUtilities import isWordBreakBefore, isWordBreakAfter


defaultOnFeatures = [
    # GSUB
    "calt",
    "ccmp", # this should always be the first feature processed
    "clig",
    "fina",
    "half", # applies only to indic
    "init",
    "isol",
    "liga",
    "locl",
    "med2", # applies only to syriac
    "medi",
    "nukt", # applies only to indic
    "pref", # applies only to khmer and myanmar
    "pres", # applies only to indic
    "pstf", # applies only to indic
    "psts",
    "rand",
    "rlig", # applies only to arabic and syriac
    "rphf", # applies only to indic
    "tjmo", # applies only to hangul
    "vatu", # applies only to indic
    "vjmo", # applies only to hangul
    # GPOS
    "abvm",  # applies only to indic
    "blwm",  # applies only to indic
    "kern",
    "mark",
    "mkmk",
    "opbd",
    "vkrn"
]


class BaseTable(object):

    def __init__(self, reversedCMAP={}):
        self.ScriptList = None
        self.FeatureList = None
        self.LookupList = None

        self._cmap = reversedCMAP

        self._featureApplicationStates = {}
        self._applicableFeatureCache = {}
        self._featureTags = None

    def loadFromFontTools(self, table, reversedCMAP, gdef):
        self._cmap = reversedCMAP
        self.ScriptList = ScriptList().loadFromFontTools(table.table.ScriptList)
        self.FeatureList = FeatureList().loadFromFontTools(table.table.FeatureList)
        self.LookupList = self._LookupListClass().loadFromFontTools(table.table.LookupList, gdef)
        self.getFeatureList()
        self._setDefaultFeatureApplicationStates()
        return self

    def setCMAP(self, reversedCMAP):
        self._cmap = reversedCMAP

    def process(self, glyphRecords, script="latn", langSys=None, logger=None):
        """
        Pass the list of GlyphRecord objects through the features
        applicable for the given script and langSys. This returns
        a list of processed GlyphRecord objects.
        """
        applicableLookups = self._preprocess(script, langSys)
        if logger:
            logger.logApplicableLookups(self, applicableLookups)
            logger.logProcessingStart()
        result = self._processLookups(glyphRecords, applicableLookups, logger=logger)
        if logger:
            logger.logProcessingEnd()
        return result

    # ------------------
    # feature management
    # ------------------

    def _setDefaultFeatureApplicationStates(self):
        """
        Activate all features defined as on by
        default in the Layout Tag Registry.
        """
        for tag in self._featureTags:
            if tag in defaultOnFeatures:
                state = True
            else:
                state = False
            self._featureApplicationStates[tag] = state

    def __contains__(self, featureTag):
        return featureTag in self._featureTags

    def getScriptList(self):
        """
        Get a list of all available scripts in the table.
        """
        found = []
        for scriptRecord in self.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            if scriptTag not in found:
                found.append(scriptTag)
        return found

    def getLanguageList(self):
        """
        Get a list of all available languages in the table.
        """
        found = []
        for scriptRecord in self.ScriptList.ScriptRecord:
            script = scriptRecord.Script
            if script.LangSysCount:
                for langSysRecord in script.LangSysRecord:
                    langSysTag = langSysRecord.LangSysTag
                    if langSysTag not in found:
                        found.append(langSysTag)
        return found

    def getFeatureList(self):
        """
        Get a list of all available features in the table.
        """
        if self._featureTags is None:
            featureList = self.FeatureList
            featureRecords = featureList.FeatureRecord
            self._featureTags = []
            for featureRecord in featureRecords:
                tag = featureRecord.FeatureTag
                if tag not in self._featureTags:
                    self._featureTags.append(tag)
        return self._featureTags

    def getFeatureState(self, featureTag):
        """
        Get a boolean representing if a feature is on or not.
        """
        return self._featureApplicationStates[featureTag]

    def setFeatureState(self, featureTag, state):
        """
        Set the application state of a feature.
        """
        self._featureApplicationStates[featureTag] = state

    # -------------
    # preprocessing
    # -------------

    def _preprocess(self, script, langSys):
        """
        Get a list of ordered (featureTag, lookupObject)
        for the given script and langSys.
        """
        # 1. get a list of applicable feature records
        #    based on the script and langSys
        features = self._getApplicableFeatures(script, langSys)
        # 2. get a list of applicable lookup tables based on the
        #    found features and the feature application states
        lookupIndexes = set()
        for feature in features:
            featureTag = feature.FeatureTag
            if not self._featureApplicationStates[featureTag]:
                continue
            featureRecord = feature.Feature
            if featureRecord.LookupCount:
                for lookupIndex in featureRecord.LookupListIndex:
                    lookupIndexes.add((lookupIndex, featureTag))
        # 3. get a list of ordered lookup records for each feature
        lookupList = self.LookupList
        lookupRecords = lookupList.Lookup
        applicableLookups = []
        for lookupIndex, featureTag in sorted(lookupIndexes):
            lookup = lookupRecords[lookupIndex]
            applicableLookups.append((featureTag, lookup))
        return applicableLookups

    def _getApplicableFeatures(self, script, langSys):
        """
        Get a list of features that apply to
        a particular script and langSys. Both
        script and langSys can be None. However,
        if script is None and no script record
        in the font is assigned to DFLT, no
        features wil be found.
        """
        # first check to see if this has already been found
        if (script, langSys) in self._applicableFeatureCache:
            return self._applicableFeatureCache[script, langSys]
        scriptList = self.ScriptList
        # 1. Find the appropriate script record
        scriptRecords = scriptList.ScriptRecord
        defaultScript = None
        applicableScript = None
        for scriptRecord in scriptRecords:
            scriptTag = scriptRecord.ScriptTag
            if scriptTag == "DFLT":
                defaultScript = scriptRecord.Script
                continue
            if scriptTag == script:
                applicableScript = scriptRecord.Script
                break
        # 2. if no suitable script record was found, return an empty list
        if applicableScript is None:
            applicableScript = defaultScript
        if applicableScript is None:
            return []
        # 3. get the applicable langSys records
        defaultLangSys = applicableScript.DefaultLangSys
        specificLangSys = None
        # if we have a langSys and the table
        # defines specific langSys behavior,
        # try to find a matching langSys record
        if langSys is not None and applicableScript.LangSysCount:
            for langSysRecord in applicableScript.LangSysRecord:
                langSysTag = langSysRecord.LangSysTag
                if langSysTag == langSys:
                    specificLangSys = langSysRecord.LangSys
                    break
        # 4. get the list of applicable features
        applicableFeatures = set()
        if specificLangSys is None:
            if defaultLangSys is not None:
                if defaultLangSys.FeatureCount:
                    applicableFeatures |= set(defaultLangSys.FeatureIndex)
                if defaultLangSys.ReqFeatureIndex != 0xFFFF:
                    applicableFeatures.add(defaultLangSys.ReqFeatureIndex)
        else:
            if specificLangSys.FeatureCount:
                applicableFeatures |= set(specificLangSys.FeatureIndex)
            if specificLangSys.ReqFeatureIndex != 0xFFFF:
                applicableFeatures.add(specificLangSys.ReqFeatureIndex)
        applicableFeatures = self._getFeatures(applicableFeatures)
        # store the found features for potential use by this method
        self._applicableFeatureCache[script, langSys] = applicableFeatures
        return applicableFeatures

    def _getFeatures(self, indices):
        """
        Get a list of ordered features located at indices.
        """
        featureList = self.FeatureList
        featureRecords = featureList.FeatureRecord
        features = [featureRecords[index] for index in sorted(indices)]
        return features

    def _getLookups(self, indices):
        """
        Get a list of ordered lookups at indices
        """
        lookupList = self.LookupList
        lookupRecords = lookupList.Lookup
        lookups = [lookupRecords[index] for index in sorted(indices)]
        return lookups

    # ----------
    # processing
    # ----------

    def _processLookups(self, glyphRecords, lookups, processingAalt=False, logger=None):
        aaltHolding = []
        boundarySensitive = set(["init", "medi", "fina", "isol"])
        for featureTag, lookup in lookups:
            # store aalt for processing at the end
            if not processingAalt and featureTag == "aalt":
                aaltHolding.append((featureTag, lookup))
                continue
            if logger:
                logger.logLookupStart(self, featureTag, lookup)
            processed = []
            # loop through the glyph records
            while glyphRecords:
                skip = False
                if featureTag in boundarySensitive:
                    side1GlyphNames = [r.getSide1GlyphNameWithUnicodeValue(self._cmap) for r in processed] + [r.getSide1GlyphNameWithUnicodeValue(self._cmap) for r in glyphRecords]
                    side2GlyphNames = [r.getSide2GlyphNameWithUnicodeValue(self._cmap) for r in processed] + [r.getSide2GlyphNameWithUnicodeValue(self._cmap) for r in glyphRecords]
                    index = len(processed)
                    wordBreakBefore = isWordBreakBefore(side1GlyphNames, index, self._cmap)
                    wordBreakAfter = isWordBreakAfter(side2GlyphNames, index, self._cmap)
                if featureTag == "init":
                    if not wordBreakBefore or wordBreakAfter:
                        skip = True
                elif featureTag == "medi":
                    if wordBreakBefore or wordBreakAfter:
                        skip = True
                elif featureTag == "fina":
                    if wordBreakBefore or not wordBreakAfter:
                        skip = True
                elif featureTag == "isol":
                    if not wordBreakBefore or not wordBreakAfter:
                        skip = True
                # loop through the lookups subtables
                performedAction = False
                if not skip:
                    processed, glyphRecords, performedAction = self._processLookup(processed, glyphRecords, lookup, featureTag, logger=logger)
                if not performedAction:
                    processed.append(glyphRecords[0])
                    glyphRecords = glyphRecords[1:]
            glyphRecords = processed
            if logger:
                logger.logLookupEnd()
        # process aalt for the final glyph records
        if not processingAalt and aaltHolding:
            glyphRecords = self._processLookups(glyphRecords, aaltHolding, processingAalt=True, logger=logger)
        return glyphRecords

    def _processLookup(self, processed, glyphRecords, lookup, featureTag, logger=None):
        performedAction = False
        for subtable in lookup.SubTable:
            if logger:
                logger.logSubTableStart(lookup, subtable)
                logger.logInput(processed, glyphRecords)
            processed, glyphRecords, performedAction = subtable.process(processed, glyphRecords, featureTag)
            if logger:
                if performedAction:
                    logger.logOutput(processed, glyphRecords)
                logger.logSubTableEnd()
            if performedAction:
                break
        return processed, glyphRecords, performedAction


class GSUB(BaseTable):

    _LookupListClass = GSUBLookupList


class GPOS(BaseTable):

    _LookupListClass = GPOSLookupList


class GDEF(object):

    def __init__(self):
        self.GlyphClassDef = None
        self.MarkAttachClassDef = None
        self.AttachList = None
        self.LigCaretList = None

    def loadFromFontTools(self, table):
        table = table.table
        if table.GlyphClassDef is not None:
            self.GlyphClassDef = GlyphClassDef().loadFromFontTools(table.GlyphClassDef)
        if table.AttachList is not None:
            self.AttachList = AttachList().loadFromFontTools(table.AttachList)
        if table.LigCaretList is not None:
            self.LigCaretList = LigCaretList().loadFromFontTools(table.LigCaretList)
        if table.MarkAttachClassDef is not None:
            self.MarkAttachClassDef = MarkAttachClassDef().loadFromFontTools(table.MarkAttachClassDef)
        return self


class AttachList(object):

    """
    Deviation from spec:
    - GlyphCount attribute is not implemented.
    """

    __slots__ = ["AttachPoint", "Coverage"]

    def __init__(self):
        self.Coverage = None
        self.AttachPoint = []

    def loadFromFontTools(self, attachList):
        self.Coverage = Coverage().loadFromFontTools(attachList.Coverage)
        for attachPoint in attachList.AttachPoint:
            attachPoint = AttachPoint().loadFromFontTools(attachPoint)
            self.AttachPoint.append(attachPoint)
        return self


class AttachPoint(object):

    """
    Deviation from spec:
    - PointCount attribute is not implemented.
    """

    __slots__ = ["PointIndex"]

    def __init__(self):
        self.PointIndex = []

    def loadFromFontTools(self, attachPoint):
        self.PointIndex = list(attachPoint.PointIndex)
        return self


class LigCaretList(object):

    """
    Deviation from spec:
    - LigGlyphCount attribute is not implemented.
    """

    __slots__ = ["LigGlyph", "Coverage"]

    def __init__(self):
        self.LigGlyph = []
        self.Coverage = None

    def loadFromFontTools(self, ligCaretList):
        self.Coverage = Coverage().loadFromFontTools(ligCaretList.Coverage)
        for ligGlyph in ligCaretList.LigGlyph:
            ligGlyph = LigGlyph().loadFromFontTools(ligGlyph)
            self.LigGlyph.append(ligGlyph)
        return self


class LigGlyph(object):

    """
    Deviation from spec:
    - CaretValueCount attribute is not implemented.
    """

    __slots__ = ["CaretValue"]

    def __init__(self):
        self.CaretValue = []

    def loadFromFontTools(self, ligGlyph):
        for caretValue in ligGlyph.CaretValue:
            format = caretValue.Format
            if format == 1:
                caretValue = CaretValueFormat1().loadFromFontTools(caretValue)
            elif format == 2:
                caretValue = CaretValueFormat2().loadFromFontTools(caretValue)
            else:
                caretValue = CaretValueFormat3().loadFromFontTools(caretValue)
            self.CaretValue.append(caretValue)
        return self


class CaretValueFormat1(object):

    __slots__ = ["CaretValueFormat", "Coordinate"]

    def __init__(self):
        self.CaretValueFormat = 1
        self.Coordinate = None

    def loadFromFontTools(self, caretValue):
        self.Coordinate = caretValue.Coordinate
        return self


class CaretValueFormat2(object):

    __slots__ = ["CaretValueFormat", "CaretValuePoint"]

    def __init__(self):
        self.CaretValueFormat = 2
        self.CaretValuePoint = None

    def loadFromFontTools(self, caretValue):
        self.CaretValuePoint = caretValue.CaretValuePoint
        return self


class CaretValueFormat3(CaretValueFormat1):

    """
    Deviation from spec:
    - DeviceTable attribute is not implemented.
    """

    __slots__ = ["CaretValueFormat", "Coordinate", "DeviceTable"]

    def __init__(self):
        super(CaretValueFormat3, self).__init__()
        self.DeviceTable = None
