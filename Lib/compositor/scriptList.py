"""
ScriptList object (and friends).
"""

__all__ = ["ScriptList", "ScriptRecord", "ScriptCount", "LangSysRecord", "LangSysCount"]

class ScriptList(object):

    __slots__ = ["ScriptCount", "ScriptRecord"]

    def __init__(self):
        self.ScriptCount = 0
        self.ScriptRecord = None

    def loadFromFontTools(self, scriptList):
        self.ScriptCount = scriptList.ScriptCount
        self.ScriptRecord = [ScriptRecord().loadFromFontTools(record) for record in scriptList.ScriptRecord]
        return self


class ScriptRecord(object):

    __slots__ = ["ScriptTag", "Script"]

    def __init__(self):
        self.ScriptTag = None
        self.Script = None

    def loadFromFontTools(self, scriptRecord):
        self.ScriptTag = scriptRecord.ScriptTag
        self.Script = Script().loadFromFontTools(scriptRecord.Script)
        return self


class Script(object):

    __slots__ = ["DefaultLangSys", "LangSysCount", "LangSysRecord"]

    def __init__(self):
        self.DefaultLangSys = None
        self.LangSysCount = 0
        self.LangSysRecord = []

    def loadFromFontTools(self, script):
        self.DefaultLangSys = LangSys().loadFromFontTools(script.DefaultLangSys)
        self.LangSysCount = script.LangSysCount
        self.LangSysRecord = [LangSysRecord().loadFromFontTools(record) for record in script.LangSysRecord]
        return self


class LangSysRecord(object):

    __slots__ = ["LangSysTag", "LangSys"]

    def __init__(self):
        self.LangSysTag = None
        self.LangSys = None

    def loadFromFontTools(self, langSysRecord):
        self.LangSysTag = langSysRecord.LangSysTag
        self.LangSys = LangSys().loadFromFontTools(langSysRecord.LangSys)
        return self


class LangSys(object):

    __slots__ = ["LookupOrder", "ReqFeatureIndex", "FeatureCount", "FeatureIndex"]

    def __init__(self):
        self.LookupOrder = None
        self.ReqFeatureIndex = None
        self.FeatureCount = 0
        self.FeatureIndex = []

    def loadFromFontTools(self, langSys):
        self.LookupOrder = langSys.LookupOrder # XXX?
        self.ReqFeatureIndex = langSys.ReqFeatureIndex
        self.FeatureCount = langSys.FeatureCount
        self.FeatureIndex = list(langSys.FeatureIndex)
        return self
