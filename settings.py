# -*- coding: utf-8 -*-


# application

# required
DEFAULT_EPSG_IN = 4326
DEFAULT_EPSG_OUT = 25833

# optional
ACCESS_CONTROL_ALLOW_ORIGIN = '*'


# Flask

# optional
JSON_AS_ASCII = False
JSON_SORT_KEYS = True
JSONIFY_MIMETYPE = 'application/json; charset=utf-8'
JSONIFY_PRETTYPRINT_REGULAR = True


# redirection URLs for HTTP error codes
REDIRECT_URL_403 = 'https://geo.sv.rostock.de/403.html'
REDIRECT_URL_404 = 'https://geo.sv.rostock.de/404.html'
REDIRECT_URL_410 = 'https://geo.sv.rostock.de/410.html'
REDIRECT_URL_500 = 'https://geo.sv.rostock.de/500.html'
REDIRECT_URL_501 = 'https://geo.sv.rostock.de/501.html'
REDIRECT_URL_502 = 'https://geo.sv.rostock.de/502.html'
REDIRECT_URL_503 = 'https://geo.sv.rostock.de/503.html'
