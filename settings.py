# -*- coding: utf-8 -*-


# application

# required

# default EPSG code for queried pair of coordinates (default EPSG code of OLC: 4326)
DEFAULT_EPSG_IN = 4326
# default EPSG code for all returned pairs of coordinates
DEFAULT_EPSG_OUT = 25833

# optional

# how to deal with Cross-Origin Resource Sharing?
ACCESS_CONTROL_ALLOW_ORIGIN = '*'


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
