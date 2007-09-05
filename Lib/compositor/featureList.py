"""
FeatureList object (and friends).
"""


__all__ = ["FeatureList", "FeatureRecord", "FeatureCount"]


class FeatureList(object):

    __slots__ = ["FeatureCount", "FeatureRecord"]

    def __init__(self, featureList):
        self.FeatureCount = featureList.FeatureCount
        self.FeatureRecord = [FeatureRecord(record) for record in featureList.FeatureRecord]


class FeatureRecord(object):

    __slots__ = ["FeatureTag", "Feature"]

    def __init__(self, featureRecord):
        self.FeatureTag = featureRecord.FeatureTag
        self.Feature = Feature(featureRecord.Feature)


class Feature(object):

    __slots__ = ["FeatureParams", "LookupCount", "LookupListIndex"]

    def __init__(self, feature):
        self.FeatureParams = feature.FeatureParams # XXX?
        self.LookupCount = feature.LookupCount
        self.LookupListIndex = list(feature.LookupListIndex)

