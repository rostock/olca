# -*- coding: utf-8 -*-

# feature collection for GeoJSON responses
class FeatureCollection(object):
  def __init__(self):
    self.features = []

  def add_features(self, features):
    self.features.extend(features)

  def as_mapping(self):
    return {
      'type': 'FeatureCollection',
      'features': self.features
    }
