# -*- coding: utf-8 -*-


# application (route /, i.e. the main entry point)

# required

# default EPSG code for queried pair of coordinates (default EPSG code of OLC: 4326)
DEFAULT_EPSG_IN = 4326
# default EPSG code for all returned pairs of coordinates
DEFAULT_EPSG_OUT = 4326
# enable querying for regional Plus codes containing municipality names (e.g. 33VX+44, Rostock)?
# also edit keys starting with MUNICIPALITY_FORWARD_ in optional section below if true!
CODE_REGIONAL_IN = True
# add an extra property to GeoJSON results with the regional Plus code containing a municipality name (e.g. 33VX+44, Rostock)?
# also edit keys starting with MUNICIPALITY_REVERSE_ in optional section below if true!
CODE_REGIONAL_OUT = True

# optional

# how to deal with Cross-Origin Resource Sharing?
ACCESS_CONTROL_ALLOW_ORIGIN = '*'
# base URL of OpenStreeMap based search engine Nominatim in forward geocoder mode (returning municipality centroids on querying municipality names)
MUNICIPALITY_FORWARD_URL = 'https://nominatim.openstreetmap.org/search?format=json'
# base URL of OpenStreeMap based search engine Nominatim in reverse geocoder mode (returning a municipality name on querying pairs of coordinates)
MUNICIPALITY_REVERSE_URL = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=10'
# proxy for querying Nominatim
# remove or comment out if not necessary!
MUNICIPALITY_PROXY = {
  'https': 'http://172.20.100.50:8080',
}


# application (route /map, i.e. the map-like entry point)

# required

# possible modes the map-like entry point can run in
MAP_MODES = ['labels']
# default mode the map-like entry point runs in
DEFAULT_MAP_MODE = 'labels'
# default EPSG code for provided bbox (default EPSG code of OLC: 4326)
DEFAULT_MAP_EPSG_IN = 4326
# default EPSG code for all returned pairs of coordinates
DEFAULT_MAP_EPSG_OUT = 4326
# pretty-print JSONified output?
DEFAULT_MAP_PRETTY = False


# Flask

# optional

# convert JSONified strings to ASCII?
JSON_AS_ASCII = False
# sort all keys in JSONified output (alphabetically)?
JSON_SORT_KEYS = True
# default MIME type of JSONified output
JSONIFY_MIMETYPE = 'application/json; charset=utf-8'
# pretty-print JSONified output?
JSONIFY_PRETTYPRINT_REGULAR = True
# redirection URLs for HTTP error codes
REDIRECT_URL_403 = 'https://geo.sv.rostock.de/403.html'
REDIRECT_URL_404 = 'https://geo.sv.rostock.de/404.html'
REDIRECT_URL_410 = 'https://geo.sv.rostock.de/410.html'
REDIRECT_URL_500 = 'https://geo.sv.rostock.de/500.html'
REDIRECT_URL_501 = 'https://geo.sv.rostock.de/501.html'
REDIRECT_URL_502 = 'https://geo.sv.rostock.de/502.html'
REDIRECT_URL_503 = 'https://geo.sv.rostock.de/503.html'
