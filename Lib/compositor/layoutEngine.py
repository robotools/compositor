from compositor.tables import GSUB, GPOS, GDEF
from compositor.glyphRecord import GlyphRecord
from compositor.cmap import reverseCMAP
from compositor.textUtilities import convertCase
from compositor.error import CompositorError
from fontTools.misc.py23 import basestring, tounicode


class LayoutEngine(object):

    def __init__(self):
        self.cmap = {}
        self.reversedCMAP = {}
        self.gdef = None
        self.gsub = None
        self.gpos = None
        self.fallbackGlyph = ".notdef"

    # ------------
    # data setting
    # ------------

    def setCMAP(self, cmap):
        self.cmap = cmap
        self.reversedCMAP = reverseCMAP(cmap)
        if self.gsub is not None:
            self.gsub.setCMAP(self.reversedCMAP)
        if self.gpos is not None:
            self.gpos.setCMAP(self.reversedCMAP)

    def setFeatureTables(self, gdef=None, gsub=None, gpos=None):
        self.gdef = None
        if gdef is not None:
            self.gdef = GDEF().loadFromFontTools(gdef)
        self.gsub = None
        if gsub is not None:
            self.gsub = GSUB().loadFromFontTools(gsub, self.reversedCMAP, self.gdef)
        self.gpos = None
        if gpos is not None:
            self.gpos = GPOS().loadFromFontTools(gpos, self.reversedCMAP, self.gdef)

    # -----------------
    # string processing
    # -----------------

    def stringToGlyphNames(self, string):
        glyphNames = []
        for c in string:
            c = tounicode(c)
            v = ord(c)
            if v in self.cmap:
                glyphNames.append(self.cmap[v])
            elif self.fallbackGlyph is not None:
                glyphNames.append(self.fallbackGlyph)
        return glyphNames

    def stringToGlyphRecords(self, string):
        return [GlyphRecord(glyphName) for glyphName in self.stringToGlyphNames(string)]

    def glyphListToGlyphRecords(self, glyphList):
        glyphRecords = []
        for glyphName in glyphList:
            record = GlyphRecord(glyphName)
            glyphRecords.append(record)
        return glyphRecords

    def process(self, stringOrGlyphList, script="latn", langSys=None, rightToLeft=False, case="unchanged", logger=None):
        if isinstance(stringOrGlyphList, basestring):
            stringOrGlyphList = self.stringToGlyphNames(stringOrGlyphList)
        if case != "unchanged":
            l = langSys
            if l is not None:
                l = l.strip()
            stringOrGlyphList = convertCase(case, stringOrGlyphList, self.cmap, self.reversedCMAP, l, self.fallbackGlyph)
        glyphRecords = self.glyphListToGlyphRecords(stringOrGlyphList)
        if rightToLeft:
            glyphRecords.reverse()
        if logger:
            logger.logStart()
            glyphNames = [r.glyphName for r in glyphRecords]
            logger.logMainSettings(glyphNames, script, langSys)
        if self.gsub is not None:
            if logger:
                logger.logTableStart(self.gsub)
            glyphRecords = self.gsub.process(glyphRecords, script=script, langSys=langSys, logger=logger)
            if logger:
                logger.logResults(glyphRecords)
                logger.logTableEnd()
        if self.gpos is not None:
            if logger:
                logger.logTableStart(self.gpos)
            glyphRecords = self.gpos.process(glyphRecords, script=script, langSys=langSys, logger=logger)
            if logger:
                logger.logResults(glyphRecords)
                logger.logTableEnd()
        if logger:
            logger.logEnd()
        return glyphRecords

    # ------------------
    # feature management
    # ------------------

    def getScriptList(self):
        gsub = []
        gpos = []
        if self.gsub is not None:
            gsub = self.gsub.getScriptList()
        if self.gpos is not None:
            gpos = self.gpos.getScriptList()
        return sorted(set(gsub + gpos))

    def getLanguageList(self):
        gsub = []
        gpos = []
        if self.gsub is not None:
            gsub = self.gsub.getLanguageList()
        if self.gpos is not None:
            gpos = self.gpos.getLanguageList()
        return sorted(set(gsub + gpos))

    def getFeatureList(self):
        gsub = []
        gpos = []
        if self.gsub is not None:
            gsub = self.gsub.getFeatureList()
        if self.gpos is not None:
            gpos = self.gpos.getFeatureList()
        return sorted(set(gsub + gpos))

    def getFeatureState(self, featureTag):
        gsubState = None
        gposState = None
        if self.gsub is not None:
            if featureTag in self.gsub:
                gsubState = self.gsub.getFeatureState(featureTag)
        if self.gpos is not None:
            if featureTag in self.gpos:
                gposState = self.gpos.getFeatureState(featureTag)
        if gsubState is not None and gposState is not None:
            if gsubState != gposState:
                raise CompositorError("Inconsistently applied feature: %s" % featureTag)
        if gsubState is not None:
            return gsubState
        if gposState is not None:
            return gposState
        raise CompositorError("Feature %s is is not contained in GSUB or GPOS" % featureTag)

    def setFeatureState(self, featureTag, state):
        if self.gsub is not None:
            if featureTag in self.gsub:
                self.gsub.setFeatureState(featureTag, state)
        if self.gpos is not None:
            if featureTag in self.gpos:
                self.gpos.setFeatureState(featureTag, state)
