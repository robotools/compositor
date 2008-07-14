import weakref
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import AbstractPen
from tables import GSUB, GPOS, GDEF
from glyphRecord import GlyphRecord
from cmap import extractCMAP, reverseCMAP
from textUtilities import convertCase

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


version = "0.0.1"


class CompositorError(Exception): pass


class Font(object):

    def __init__(self, path, glyphClass=None):
        self.path = path
        self.fallbackGlyph = ".notdef"
        self._glyphs = {}
        self.source = TTFont(path)
        self.loadGlyphSet()
        self.loadInfo()
        self.loadCMAP()
        self.loadFeatures()
        if glyphClass is None:
            glyphClass = Glyph
        self.glyphClass = glyphClass

    def __del__(self):
        del self._glyphs
        self.source.close()
        del self.source

    # --------------
    # initialization
    # --------------

    def loadCMAP(self):
        self.cmap = extractCMAP(self.source)
        self.reversedCMAP = reverseCMAP(self.cmap)

    def loadGlyphSet(self):
        self.glyphSet = self.source.getGlyphSet()
        # the glyph order will be needed later
        # to assign the proper glyph index to
        # glyph objects.
        order = self.source.getGlyphOrder()
        self._glyphOrder = {}
        for index, glyphName in enumerate(order):
            self._glyphOrder[glyphName] = index

    def loadInfo(self):
        self.info = info = Info()
        head = self.source["head"]
        hhea = self.source["hhea"]
        os2 = self.source["OS/2"]
        info.unitsPerEm = head.unitsPerEm
        info.ascender = hhea.ascent
        info.descender = hhea.descent
        info.xHeight = os2.sxHeight
        info.capHeight = os2.sCapHeight
        # names
        nameIDs = {}
        for nameRecord in self.source["name"].names:
            nameID = nameRecord.nameID
            platformID = nameRecord.platformID
            platEncID = nameRecord.platEncID
            langID = nameRecord.langID
            text = nameRecord.string
            nameIDs[nameID, platformID, platEncID, langID] = text
        # to retrive the family and style names, first start
        # with the preferred name entries and progress to less
        # specific entries until something is found.
        familyPriority = [(16, 1, 0, 0), (16, 1, None, None), (16, None, None, None),
                        (1, 1, 0, 0), (1, 1, None, None), (1, None, None, None)]
        familyName = self._skimNameIDs(nameIDs, familyPriority)
        stylePriority = [(17, 1, 0, 0), (17, 1, None, None), (17, None, None, None),
                        (2, 1, 0, 0), (2, 1, None, None), (2, None, None, None)]
        styleName = self._skimNameIDs(nameIDs, stylePriority)
        if familyName is None or styleName is None:
            raise CompositorError("Could not extract name data from name table.")
        self.info.familyName = familyName
        self.info.styleName = styleName

    def _skimNameIDs(self, nameIDs, priority):
        for (nameID, platformID, platEncID, langID) in priority:
            for (nID, pID, pEID, lID), text in nameIDs.items():
                if nID != nameID:
                    continue
                if pID != platformID and platformID is not None:
                    continue
                if pEID != platEncID and platEncID is not None:
                    continue
                if lID != langID and langID is not None:
                    continue
                # make sure there are no endian issues
                # XXX right way to do this?
                text = "".join([i for i in text if i != "\x00"])
                return text

    def loadFeatures(self):
        self.gsub = None
        self.gpos = None
        self.gdef = None
        if self.source.has_key("GDEF"):
            self.gdef = GDEF().loadFromFontTools(self.source["GDEF"])
        if self.source.has_key("GSUB"):
            self.gsub = GSUB().loadFromFontTools(self.source["GSUB"], self.reversedCMAP, self.gdef)
        if self.source.has_key("GPOS"):
            self.gpos = GPOS().loadFromFontTools(self.source["GPOS"], self.reversedCMAP, self.gdef)

    # -------------
    # dict behavior
    # -------------

    def keys(self):
        return self.glyphSet.keys()

    def __contains__(self, name):
        return self.glyphSet.has_key(name)

    def __getitem__(self, name):
        if name not in self._glyphs:
            glyph = self.glyphSet[name]
            index = self._glyphOrder[name]
            glyph = self.glyphClass(name, index, glyph, self)
            self._glyphs[name] = glyph
        return self._glyphs[name]

    # -----------------
    # string processing
    # -----------------

    def stringToGlyphNames(self, string):
        glyphNames = []
        for c in string:
            c = unicode(c)
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
            if glyphName not in self:
                if self.fallbackGlyph is None:
                    continue
                glyphName = self.fallbackGlyph
            glyphRecords.append(GlyphRecord(glyphName))
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

    # -------------
    # Miscellaneous
    # -------------

    def getGlyphOrder(self):
        return self.source.getGlyphOrder()


class Info(object): pass


class Glyph(object):

    def __init__(self, name, index, source, font):
        # the char string must be loaded by drawing it
        if not hasattr(source, "width"):
            source.draw(_GlyphLoadPen())
        self.name = name
        self.source = source
        self.width = source.width
        self.font = weakref.ref(font)
        self.index = index

    def draw(self, pen):
        self.source.draw(pen)

    def _getBounds(self):
        from fontTools.pens.boundsPen import BoundsPen
        pen = BoundsPen(self.font())
        self.draw(pen)
        return pen.bounds
    bounds = property(_getBounds)


class _GlyphLoadPen(AbstractPen):

    def __init__(self):
        pass

    def moveTo(self, pt):
        pass

    def lineTo(self, pt):
        pass

    def curveTo(self, *points):
        pass

    def qCurveTo(self, *points):
        pass

    def addComponent(self, glyphName, transformation):
        pass

    def closePath(self):
        pass

    def endPath(self):
        pass

