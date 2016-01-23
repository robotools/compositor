"""
A simple logging object. It reports, with
the help of the Compositor objects, a
wide range of data about the processing
of a string of text for a font.

Usage:

    logger = Logger()
    logger.logStart()
    font = Font("/path/to/a/font.otf")
    font.process("Hello World!", logger=logger)
    logger.logEnd()
    report = logger.getText()

The returned log is in XML format.
"""

from fontTools.misc.py23 import StringIO
from xmlWriter import XMLWriter


class Logger(object):

    def __init__(self):
        self._file = StringIO()
        self._writer = XMLWriter(self._file, encoding="utf-8")

    def __del__(self):
        self._writer = None
        self._file.close()

    def logStart(self):
        self._writer.begintag("xml")

    def logEnd(self):
        self._writer.endtag("xml")

    def logMainSettings(self, glyphNames, script, langSys):
        self._writer.begintag("initialSettings")
        self._writer.newline()
        self._writer.simpletag("string", value=" ".join(glyphNames))
        self._writer.newline()
        self._writer.simpletag("script", value=script)
        self._writer.newline()
        self._writer.simpletag("langSys", value=langSys)
        self._writer.newline()
        self._writer.endtag("initialSettings")
        self._writer.newline()

    def logTableStart(self, table):
        name = table.__class__.__name__
        self._writer.begintag("table", name=name)
        self._writer.newline()
        self.logTableFeatureStates(table)

    def logTableEnd(self):
        self._writer.endtag("table")

    def logTableFeatureStates(self, table):
        self._writer.begintag("featureStates")
        self._writer.newline()
        for tag in sorted(table.getFeatureList()):
            state = table.getFeatureState(tag)
            self._writer.simpletag("feature", name=tag, state=int(state))
            self._writer.newline()
        self._writer.endtag("featureStates")
        self._writer.newline()

    def logApplicableLookups(self, table, lookups):
        self._writer.begintag("applicableLookups")
        self._writer.newline()
        if lookups:
            order = []
            last = None
            for tag, lookup in lookups:
                if tag != last:
                    if order:
                        self._logLookupList(last, order)
                    order = []
                    last = tag
                index = table.LookupList.Lookup.index(lookup)
                order.append(index)
            self._logLookupList(last, order)
        self._writer.endtag("applicableLookups")
        self._writer.newline()

    def _logLookupList(self, tag, lookups):
        lookups = " ".join([str(i) for i in lookups])
        self._writer.simpletag("lookups", feature=tag, indices=lookups)
        self._writer.newline()

    def logProcessingStart(self):
        self._writer.begintag("processing")
        self._writer.newline()

    def logProcessingEnd(self):
        self._writer.endtag("processing")
        self._writer.newline()

    def logLookupStart(self, table, tag, lookup):
        index = table.LookupList.Lookup.index(lookup)
        self._writer.begintag("lookup", feature=tag, index=index)
        self._writer.newline()

    def logLookupEnd(self):
        self._writer.endtag("lookup")
        self._writer.newline()

    def logSubTableStart(self, lookup, subtable):
        index = lookup.SubTable.index(subtable)
        lookupType = subtable.__class__.__name__
        self._writer.begintag("subTable", index=index, type=lookupType)
        self._writer.newline()

    def logSubTableEnd(self):
        self._writer.endtag("subTable")
        self._writer.newline()

    def logGlyphRecords(self, glyphRecords):
        for r in glyphRecords:
            self._writer.simpletag("glyphRecord", name=r.glyphName,
                xPlacement=r.xPlacement, yPlacement=r.yPlacement,
                xAdvance=r.xAdvance, yAdvance=r.yAdvance)
            self._writer.newline()

    def logInput(self, processed, unprocessed):
        self._writer.begintag("input")
        self._writer.newline()
        self._writer.begintag("processed")
        self._writer.newline()
        self.logGlyphRecords(processed)
        self._writer.endtag("processed")
        self._writer.newline()
        self._writer.begintag("unprocessed")
        self._writer.newline()
        self.logGlyphRecords(unprocessed)
        self._writer.endtag("unprocessed")
        self._writer.newline()
        self._writer.endtag("input")
        self._writer.newline()

    def logOutput(self, processed, unprocessed):
        self._writer.begintag("output")
        self._writer.newline()
        self._writer.begintag("processed")
        self._writer.newline()
        self.logGlyphRecords(processed)
        self._writer.endtag("processed")
        self._writer.newline()
        self._writer.begintag("unprocessed")
        self._writer.newline()
        self.logGlyphRecords(unprocessed)
        self._writer.endtag("unprocessed")
        self._writer.newline()
        self._writer.endtag("output")
        self._writer.newline()

    def logResults(self, processed):
        self._writer.begintag("results")
        self._writer.newline()
        self.logGlyphRecords(processed)
        self._writer.endtag("results")
        self._writer.newline()

    def getText(self):
        return self._file.getvalue()
