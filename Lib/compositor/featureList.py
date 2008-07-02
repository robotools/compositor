"""
FeatureList object (and friends).
"""


__all__ = ["FeatureList", "FeatureRecord", "FeatureCount"]


class FeatureList(object):

    __slots__ = ["FeatureCount", "FeatureRecord"]

    def __init__(self):
        self.FeatureCount = 0
        self.FeatureRecord = []

    def loadFromFontTools(self, featureList):
        self.FeatureCount = featureList.FeatureCount
        self.FeatureRecord = []
        self.FeatureRecord = [FeatureRecord().loadFromFontTools(record) for record in featureList.FeatureRecord]
        return self


class FeatureRecord(object):

    __slots__ = ["FeatureTag", "Feature"]

    def __init__(self):
        self.FeatureTag = None
        self.Feature = None

    def loadFromFontTools(self, featureRecord):
        self.FeatureTag = featureRecord.FeatureTag
        self.Feature = Feature().loadFromFontTools(featureRecord.Feature)
        return self


class Feature(object):

    __slots__ = ["FeatureParams", "LookupCount", "LookupListIndex"]

    def __init__(self):
        self.FeatureParams = None
        self.LookupCount = 0
        self.LookupListIndex = []

    def loadFromFontTools(self, feature):
        self.FeatureParams = feature.FeatureParams # XXX?
        self.LookupCount = feature.LookupCount
        self.LookupListIndex = list(feature.LookupListIndex)
        return self

