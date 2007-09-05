"""
ScriptList object (and friends).
"""

__all__ = ["ScriptList", "ScriptRecord", "ScriptCount", "LangSysRecord", "LangSysCount"]

class ScriptList(object):

    __slots__ = ["ScriptCount", "ScriptRecord"]

    def __init__(self, scriptList):
        self.ScriptCount = scriptList.ScriptCount
        self.ScriptRecord = [ScriptRecord(record) for record in scriptList.ScriptRecord]


class ScriptRecord(object):

    __slots__ = ["ScriptTag", "Script"]

    def __init__(self, scriptRecord):
        self.ScriptTag = scriptRecord.ScriptTag
        self.Script = Script(scriptRecord.Script)


class Script(object):

    __slots__ = ["DefaultLangSys", "LangSysCount", "LangSysRecord"]

    def __init__(self, script):
        self.DefaultLangSys = LangSys(script.DefaultLangSys)
        self.LangSysCount = script.LangSysCount
        self.LangSysRecord = [LangSysRecord(record) for record in script.LangSysRecord]


class LangSysRecord(object):

    __slots__ = ["LangSysTag", "LangSys"]

    def __init__(self, langSysRecord):
        self.LangSysTag = langSysRecord.LangSysTag
        self.LangSys = LangSys(langSysRecord.LangSys)


class LangSys(object):

    __slots__ = ["LookupOrder", "ReqFeatureIndex", "FeatureCount", "FeatureIndex"]

    def __init__(self, langSys):
        self.LookupOrder = langSys.LookupOrder # XXX?
        self.ReqFeatureIndex = langSys.ReqFeatureIndex
        self.FeatureCount = langSys.FeatureCount
        self.FeatureIndex = list(langSys.FeatureIndex)
