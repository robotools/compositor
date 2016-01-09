import weakref
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import AbstractPen
from layoutEngine import LayoutEngine
from cmap import extractCMAP
from error import CompositorError


class Font(LayoutEngine):

    def __init__(self, path, glyphClass=None):
        self.path = path
        self._glyphs = {}
        if isinstance(path, TTFont):
            self.source = path
        else:
            self.source = TTFont(path)
        self.loadGlyphSet()
        self.loadCMAP()
        self.loadFeatures()
        self.loadInfo()
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
        cmap = extractCMAP(self.source)
        self.setCmap(self.cmap)

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
        # stylistic set names
        self.stylisticSetNames = {}
        if self.gsub:
            for featureRecord in self.gsub.FeatureList.FeatureRecord:
                params = featureRecord.Feature.FeatureParams
                if hasattr(params, "UINameID"):
                    ssNameID = params.UINameID
                    namePriority = [(ssNameID, 1, 0, 0), (ssNameID, 1, None, None), (ssNameID, 3, 1, 1033), (ssNameID, 3, None, None)]
                    ssName = self._skimNameIDs(nameIDs, namePriority)
                    if ssName:
                        self.stylisticSetNames[featureRecord.FeatureTag] = ssName

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
        gdef = None
        if self.source.has_key("GDEF"):
            gdef = self.source["GDEF"]
        gsub = None
        if self.source.has_key("GSUB"):
            gsub = self.source["GSUB"]
        gpos = None
        if self.source.has_key("GPOS"):
            gpos = self.source["GPOS"]
        self.setFeatureTables(gdef, gsub, gpos)

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

    # -------------
    # Miscellaneous
    # -------------

    def getGlyphOrder(self):
        return self.source.getGlyphOrder()

    def process(self, *args, **kwargs):
        glyphRecords = super(Font, self).process(*args, **kwargs)
        for glyphRecord in glyphRecords:
            glyphRecord.advanceWidth += self[glyphRecord.glyphName].width
        return glyphRecords


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
