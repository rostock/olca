# -*- coding: utf-8 -*-

from flask import Flask, jsonify, redirect, request
from flask_compress import Compress
from urllib import quote_plus, unquote
import math
import openlocationcode as olc
import pyproj as p
import requests as req
import re



# global constants
HTTP_OK_STATUS_ = 200
HTTP_ERROR_STATUS_ = 400
DEFAULT_ERROR_MESSAGE_ = 'value of required \'query\' parameter is neither a valid pair of coordinates (required order: longitude/x,latitude/y) nor a valid Plus code'
DEFAULT_MAP_ERROR_MESSAGE_ = 'value of required \'bbox\' parameter is not a valid quadruple of coordinates (required order: southwest longitude/x,southwest latitude/y,northeast longitude/x,northeast latitude/y)'
SEPARATOR_ = ','
OLC_EPSG_ = 4326
OLC_PRECISION_ = len(str(0.000125)[2:])
EARTH_RADIUS_ = 6371 # kilometers



# initialise application
app = Flask(__name__)



# import configurations from files
app.config.from_pyfile('secrets.py', silent = True)
app.config.from_pyfile('settings.py', silent = True)



# initialise Compress
Compress(app)



# custom functions

# request handler
def request_handler(request, arg_name):

  # cover GET method
  if request.method == 'GET' and arg_name in request.args:
    return request.args[arg_name]
  else:
    # cover POST method with form body
    if request.method == 'POST' and arg_name in request.form:
      return request.form[arg_name]
    else:
      # read JSON data (just in case JSON data is provided via POST)
      request_data = request.get_json()
      # cover POST method with JSON data
      if request.method == 'POST' and request_data is not None and arg_name in request_data:
        return request_data[arg_name]


# EPSG transformation handler
def epsg_handler(epsg_in, epsg_out, source_x, source_y):

  source_projection = p.Proj(init = 'epsg:' + str(epsg_in)) if epsg_out is None else p.Proj(init = 'epsg:' + str(OLC_EPSG_))
  target_projection = p.Proj(init = 'epsg:' + str(OLC_EPSG_)) if epsg_out is None else p.Proj(init = 'epsg:' + str(epsg_out))
  return p.transform(source_projection, target_projection, source_x, source_y)


# distance handler
def distance_handler(from_point_x, from_point_y, to_point_x, to_point_y):
    
    # calculate the great circle distance of two geographical points
    from_point_x, from_point_y, to_point_x, to_point_y = map(math.radians, [from_point_x, from_point_y, to_point_x, to_point_y])
    dlon = to_point_x - from_point_x
    dlat = to_point_y - from_point_y
    a = math.sin(dlat / 2) ** 2 + math.cos(from_point_y) * math.cos(to_point_y) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_ * math.asin(math.sqrt(a))


# Open Location Code (OLC) handler
def olc_handler(x, y, query, epsg_in, epsg_out, code_regional):

  # if necessary...
  if code_regional:
    # decode queried regional Plus code if it is valid, return an error if not
    municipality_centroid_x, municipality_centroid_y = municipality_forward_handler(query[1])
    try:
      query = olc.recoverNearest(query[0], municipality_centroid_y, municipality_centroid_x)
    except:
      return { 'message': 'provided regional Plus code is not valid', 'status': HTTP_ERROR_STATUS_ }, HTTP_ERROR_STATUS_
  
  # if a pair of coordinates was queried...
  if query is None:
    # transform if EPSG code of queried pair of coordinates is not equal to default EPSG code of OLC
    if epsg_in != OLC_EPSG_:
      try:
        x, y = epsg_handler(epsg_in, None, x, y)
      except:
        return { 'message': 'transformation of provided pair of coordinates (required order: longitude/x,latitude/y) not possible', 'status': HTTP_ERROR_STATUS_ }, HTTP_ERROR_STATUS_
    # encode queried pair of coordinates
    code = olc.encode(y, x)
  # if not...
  else:
    # take query as the Plus code
    code = query

  # take care of short Plus code if necessary
  code = code.split(olc.SEPARATOR_)[0].ljust(8, olc.PADDING_CHARACTER_) + olc.SEPARATOR_ if olc.isShort(code) else code
  
  # determine the level
  level = len(code.replace(olc.SEPARATOR_, '').rstrip(olc.PADDING_CHARACTER_)) / 2

  # decode the Plus code to calculate the center pair of coordinates and the bbox
  coord = olc.decode(code)
  center_x, center_y = coord.longitudeCenter, coord.latitudeCenter
  bbox_sw_x, bbox_sw_y = coord.longitudeLo, coord.latitudeLo
  bbox_ne_x, bbox_ne_y = coord.longitudeHi, coord.latitudeHi

  # get the full Plus code
  code = olc.encode(center_y, center_x)
  
  # transform all pairs of coordinates to be returned if EPSG code for all returned pairs of coordinates is not equal to default EPSG code of OLC, round to six decimals if not
  if epsg_out != OLC_EPSG_:
    try:
      center_x, center_y = epsg_handler(None, epsg_out, center_x, center_y)
      bbox_sw_x, bbox_sw_y = epsg_handler(None, epsg_out, bbox_sw_x, bbox_sw_y)
      bbox_ne_x, bbox_ne_y = epsg_handler(None, epsg_out, bbox_ne_x, bbox_ne_y)
    except Exception as e:
      return { 'message': str(e), 'status': HTTP_ERROR_STATUS_ }, HTTP_ERROR_STATUS_
  else:
    center_x, center_y = round(center_x, OLC_PRECISION_), round(center_y, OLC_PRECISION_)
    bbox_sw_x, bbox_sw_y = round(bbox_sw_x, OLC_PRECISION_), round(bbox_sw_y, OLC_PRECISION_)
    bbox_ne_x, bbox_ne_y = round(bbox_ne_x, OLC_PRECISION_), round(bbox_ne_y, OLC_PRECISION_)

  # build the bbox
  bbox = [
    [
      [ bbox_sw_x, bbox_sw_y ],
      [ bbox_ne_x, bbox_sw_y ],
      [ bbox_ne_x, bbox_ne_y ],
      [ bbox_sw_x, bbox_ne_y ],
      [ bbox_sw_x, bbox_sw_y ]
    ]
  ]

  # build the properties
  properties = {
    # longitude/x of the center pair of coordinates
    'center_x': center_x,
    # latitude/y of the center pair of coordinates
    'center_y': center_y,
    # grid level 1 code
    'code_level_1': olc.encode(coord.latitudeCenter, coord.longitudeCenter, 2),
    'epsg_in': epsg_in,
    'epsg_out': epsg_out,
    # grid level
    'level': level
  }
  if level > 1:
    # grid level 2 code
    properties.update( { 'code_level_2': olc.encode(coord.latitudeCenter, coord.longitudeCenter, 4) } )
  if level > 2:
    # grid level 3 code
    properties.update( { 'code_level_3': olc.encode(coord.latitudeCenter, coord.longitudeCenter, 6) } )
  if level > 3:
    # grid level 4 code
    properties.update( { 'code_level_4': olc.encode(coord.latitudeCenter, coord.longitudeCenter, 8) } )
  if level > 4:
    # grid level 5 code, local code and short code (depending on the distance between the code center and the reference pair of coordinates)
    code_local = code[4:]
    properties.update( { 'code_level_5': code, 'code_local': code_local, 'code_short': olc.shorten(code, y, x) if query is None else olc.shorten(code, coord.latitudeCenter, coord.longitudeCenter) } )
    # get all information for adding the regional Plus code if necessary
    if app.config['CODE_REGIONAL_OUT']:
      properties.update( { 'code_regional': municipality_reverse_handler(coord.longitudeCenter, coord.latitudeCenter, code_local) } )

  # valid GeoJSON
  return {
    'type': 'Feature',
    'properties': properties,
    'geometry': {
      'type': 'Polygon',
      'coordinates': bbox
    }
  }, HTTP_OK_STATUS_


# OLC loop handler
def olc_loop_handler(min_x, min_y, max_x, max_y, epsg_in, epsg_out, mode):
  
  # return points only if in labels mode, polygons if not
  if mode == 'labels':
    points_only = True
  else:
    points_only = False

  # transform if EPSG code of input min/max x/y is not equal to default EPSG code of OLC
  if epsg_in != OLC_EPSG_:
    try:
      min_x, min_y = epsg_handler(epsg_in, None, min_x, min_y)
      max_x, max_y = epsg_handler(epsg_in, None, max_x, max_y)
    except:
      return { 'message': 'transformation of provided quadruple of coordinates (required order: southwest longitude/x,southwest latitude/y,northeast longitude/x,northeast latitude/y) not possible', 'status': HTTP_ERROR_STATUS_ }, HTTP_ERROR_STATUS_

  # calculate the OLC level the loop encoding will take place within
  distance = distance_handler(min_x, min_y, max_x, max_y)
  if distance <= 0.75:
    level = 5
  elif distance <= 7.5:
    level = 4
  elif distance <= 150:
    level = 3
  elif distance <= 1500:
    level = 2
  else:
    level = 1
  # calculate the OLC level resolution value
  level_resolution = olc.PAIR_RESOLUTIONS_[level - 1]
  # calculate the OLC code length
  code_length = level * 2
  # calculate the precision of level resolution
  level_resolution_precision = len(str(level_resolution - int(level_resolution))[2:])
  # calculate the buffer in degrees to prevent multiple encodings
  buffer = 10**-(level_resolution_precision) if level_resolution_precision > 1 else 1
  # calculate the number of lines (of encodings)
  num_lines = int(math.ceil((round(round(max_y, level_resolution_precision) - round(min_y, level_resolution_precision), level_resolution_precision)) / level_resolution))
  # calculate the number of rows (of encodings)
  num_rows = int(math.ceil((round(round(max_x, level_resolution_precision) - round(min_x, level_resolution_precision), level_resolution_precision)) / level_resolution))
  
  # prepare list to fill with data and to finally return later on
  data_list = []
  
  # loop through all lines
  for line in range(num_lines):
    # calculate current y
    y = min_y + (level_resolution * line) + buffer
    # loop through all rows
    for row in range(num_rows):
      # calculate current x
      x = min_x + (level_resolution * row) + buffer
      # encode
      code = olc.encode(y, x, code_length)
      # decode again to calculate the center pair of coordinates
      coord = olc.decode(code)
      center_x, center_y = coord.longitudeCenter, coord.latitudeCenter
      # transform all pairs of coordinates to be returned if EPSG code for all returned pairs of coordinates is not equal to default EPSG code of OLC, round to six decimals if not
      if epsg_out != OLC_EPSG_:
        try:
          center_x, center_y = epsg_handler(None, epsg_out, center_x, center_y)
        except Exception as e:
          return { 'message': str(e), 'status': HTTP_ERROR_STATUS_ }, HTTP_ERROR_STATUS_
      else:
        center_x, center_y = round(center_x, OLC_PRECISION_), round(center_y, OLC_PRECISION_)
      # build the label
      if code_length == 10:
          label = code[9:11]
      elif code_length == 8:
          label = code[:4] + '\n' + code[4:]
      elif code_length == 6:
          label = code[:4] + '\n' + code[4:6]
      else:
          label = code[:code_length]
      # build the properties
      properties = {
        # label
        'label': label,
        # code
        'code': code,
        # grid level
        'level': level
      }
      # valid GeoJSON
      if points_only:
        data = {
          'type': 'Feature',
          'properties': properties,
          'geometry': {
            'type': 'Point',
            'coordinates': [ center_x, center_y ]
          }
        }
      else:
        data = {}
      data_list.append(data)

  return data_list, HTTP_OK_STATUS_


# response handler
def response_handler(data, status):

  # always JSON
  response = jsonify(data)

  # CORS response header indicating whether the response can be shared with requesting code from the given origin:
  # set to corresponding value if provided in settings
  if 'ACCESS_CONTROL_ALLOW_ORIGIN' in app.config:
    response.headers['Access-Control-Allow-Origin'] = app.config['ACCESS_CONTROL_ALLOW_ORIGIN']
  return response, status


# multiple GeoJSON features (i.e. within a FeatureCollection) handler
def multiple_features_handler(data):

  return {
    'type': 'FeatureCollection',
    'features': data
  }


# municipality reverse search handler
def municipality_reverse_handler(x, y, code_local):

  # get Nominatim base URL in reverse geocoder mode (returning a municipality name on querying pairs of coordinates) from settings
  municipality_reverse_url = app.config['MUNICIPALITY_REVERSE_URL']

  # build the query string
  query = '&lon=' + str(x) + '&lat=' + str(y)

  # query Nominatim (via proxy if necessary) and return the municipality name
  try:
    response = req.get(municipality_reverse_url + query, proxies = app.config['MUNICIPALITY_PROXY']).json() if 'MUNICIPALITY_PROXY' in app.config else req.get(municipality_reverse_url + query).json()
    return code_local + ', ' + response['name']
  except:
    return 'not definable'


# municipality forward search handler
def municipality_forward_handler(municipality_name):

  # get Nominatim base URL in forward geocoder mode (returning municipality centroids on querying municipality names) from settings
  municipality_forward_url = app.config['MUNICIPALITY_FORWARD_URL']

  # build the query string
  query = '&city=' + municipality_name

  # query Nominatim (via proxy if necessary), process the response and return the centroid pair of coordinates of the first municipality found
  try:
    response = req.get(municipality_forward_url + query, proxies = app.config['MUNICIPALITY_PROXY']).json() if 'MUNICIPALITY_PROXY' in app.config else req.get(municipality_forward_url + query).json()
    for response_item in response:
      if response_item['type'] == 'administrative' or response_item['type'] == 'city' or response_item['type'] == 'town':
        return float(response_item['lon']), float(response_item['lat'])
    return None, None
  except:
    return None, None




# routing
@app.route('/', methods=['GET', 'POST'])
def query():

  # request handling

  # required query parameter, i.e. what to look for:
  # set to corresponding value if provided via request arguments, return an error if not
  handled_request = request_handler(request, 'query')
  if handled_request is not None:
    # careful with the plus sign!
    query = unquote(quote_plus(handled_request.encode('utf-8')))
  else:
    data = { 'message': 'missing required \'query\' parameter or parameter empty', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # optional EPSG code parameter for queried pair of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_in')
  if handled_request is not None:
    # a little trick here: only look for digits in the parameter
    if bool(re.search(r'\d', handled_request)):
      epsg_in = re.findall('\d+', handled_request)[0]
    else:
      epsg_in = handled_request
  else:
    epsg_in = app.config['DEFAULT_EPSG_IN']

  # optional EPSG code parameter for all returned pairs of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_out')
  if handled_request is not None:
    # a little trick here: only look for digits in the parameter
    if bool(re.search(r'\d', handled_request)):
      epsg_out = re.findall('\d+', handled_request)[0]
    else:
      epsg_out = handled_request
  else:
    epsg_out = app.config['DEFAULT_EPSG_OUT']

  # query processing

  # return an error if optional EPSG code parameter for queried pair of coordinates is not a number
  try:
    epsg_in = int(epsg_in)
  except ValueError:
    data = { 'message': 'value of optional \'epsg_in\' parameter is not a number', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # return an error if optional EPSG code parameter for all returned pairs of coordinates is not a number
  try:
    epsg_out = int(epsg_out)
  except ValueError:
    data = { 'message': 'value of optional \'epsg_out\' parameter is not a number', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # required query parameter, i.e. what to look for:
  if SEPARATOR_ in query:
    # if necessary: decode queried regional Plus code if it is valid, return an error if not
    if app.config['CODE_REGIONAL_IN'] and olc.SEPARATOR_ in query:
      query = query.split(SEPARATOR_)
      if olc.SEPARATOR_ in query[0]:
        code = query[0]
        municipality_name = query[1]
      elif olc.SEPARATOR_ in query[1]:
        code = query[1]
        municipality_name = query[0]
      else:
        data = { 'message': DEFAULT_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
        return response_handler(data, HTTP_ERROR_STATUS_)
      try:
        data, status = olc_handler(None, None, [code, municipality_name], epsg_in, epsg_out, True)
        return response_handler(data, status)
      except:
        data = { 'message': DEFAULT_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
        return response_handler(data, HTTP_ERROR_STATUS_)
    # encode queried pair of coordinates if they are valid, return an error if not
    else:
      query = query.split(SEPARATOR_)
      try:
        data, status = olc_handler(float(query[0]), float(query[1]), None, epsg_in, epsg_out, False)
        return response_handler(data, status)
      except:
        data = { 'message': DEFAULT_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
        return response_handler(data, HTTP_ERROR_STATUS_)
  # decode queried Plus code if it is valid, return an error if not
  else:
    try:
      data, status = olc_handler(None, None, query, epsg_in, epsg_out, False)
      return response_handler(data, status)
    except:
      data = { 'message': DEFAULT_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
      return response_handler(data, HTTP_ERROR_STATUS_)


@app.route('/map', methods=['GET', 'POST'])
def map_query():

  # request handling

  # required bbox parameter, i.e. the bbox the request is relevant for:
  # set to corresponding value if provided via request arguments, return an error if not
  handled_request = request_handler(request, 'bbox')
  if handled_request is not None:
    bbox = handled_request
  else:
    data = { 'message': 'missing required \'bbox\' parameter or parameter empty', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # optional mode parameter, i.e. which mode to run in:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'mode')
  if handled_request is not None and handled_request in app.config['MAP_MODES']:
    mode = handled_request
  else:
    mode = app.config['DEFAULT_MAP_MODE']

  # optional EPSG code parameter for provided bbox:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_in')
  if handled_request is not None:
    # a little trick here: only look for digits in the parameter
    if bool(re.search(r'\d', handled_request)):
      epsg_in = re.findall('\d+', handled_request)[0]
    else:
      epsg_in = handled_request
  else:
    epsg_in = app.config['DEFAULT_MAP_EPSG_IN']

  # optional EPSG code parameter for all returned pairs of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_out')
  if handled_request is not None:
    # a little trick here: only look for digits in the parameter
    if bool(re.search(r'\d', handled_request)):
      epsg_out = re.findall('\d+', handled_request)[0]
    else:
      epsg_out = handled_request
  else:
    epsg_out = app.config['DEFAULT_MAP_EPSG_OUT']

  # optional pretty parameter, i.e. whether to pretty-print JSONified output or not:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'pretty')
  if handled_request is not None and (handled_request in [0, 1, False, True, '0', '1', 'f', 't', 'False', 'True', 'false', 'true', 'n', 'y', 'no', 'yes']):
    if handled_request in [0, '0', 'f', 'False', 'false', 'n', 'no']:
      pretty = False
    elif handled_request in [1, '1', 't', 'True', 'true', 'y', 'yes']:
      pretty = True
    else:
      pretty = handled_request
  else:
    pretty = app.config['DEFAULT_MAP_PRETTY']

  # query processing

  # return an error if optional EPSG code parameter for provided bbox is not a number
  try:
    epsg_in = int(epsg_in)
  except ValueError:
    data = { 'message': 'value of optional \'epsg_in\' parameter is not a number', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # return an error if optional EPSG code parameter for all returned pairs of coordinates is not a number
  try:
    epsg_out = int(epsg_out)
  except ValueError:
    data = { 'message': 'value of optional \'epsg_out\' parameter is not a number', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # required bbox parameter, i.e. the bbox the request is relevant for:
  bbox = bbox.split(SEPARATOR_)
  # if bbox is valid: determine southwest longitude/x,southwest latitude/y,northeast longitude/x,northeast latitude/y if possible, return an error if not
  if len(bbox) == 4 and bbox[0] is not None and bbox[1] is not None and bbox[2] is not None and bbox[3] is not None:
    try:
      bbox_sw_x, bbox_sw_y = float(bbox[0]), float(bbox[1])
      bbox_ne_x, bbox_ne_y = float(bbox[2]), float(bbox[3])
      # if bbox is really a bbox: loop through bbox and encode all pairs of coordinates if possible, return an error if not
      if bbox_ne_x >= bbox_sw_x and bbox_ne_y >= bbox_sw_y:
        data_list, status = olc_loop_handler(bbox_sw_x, bbox_sw_y, bbox_ne_x, bbox_ne_y, epsg_in, epsg_out, mode)
        if pretty:
          app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        else:
          app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        return response_handler(multiple_features_handler(data_list), status)
      else:
        data = { 'message': DEFAULT_MAP_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
        return response_handler(data, HTTP_ERROR_STATUS_)
    except:
      data = { 'message': DEFAULT_MAP_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
      return response_handler(data, HTTP_ERROR_STATUS_)
  else:
    data = { 'message': DEFAULT_MAP_ERROR_MESSAGE_, 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)



# custom error handling
if 'REDIRECT_URL_403' in app.config:
  @app.errorhandler(403)
  def error_403(error):
    return redirect(app.config['REDIRECT_URL_403'])

if 'REDIRECT_URL_404' in app.config:
  @app.errorhandler(404)
  def error_404(error):
    return redirect(app.config['REDIRECT_URL_404'])

if 'REDIRECT_URL_410' in app.config:
  @app.errorhandler(410)
  def error_410(error):
    return redirect(app.config['REDIRECT_URL_410'])

if 'REDIRECT_URL_500' in app.config:
  @app.errorhandler(500)
  def error_500(error):
    return redirect(app.config['REDIRECT_URL_500'])

if 'REDIRECT_URL_501' in app.config:
  @app.errorhandler(501)
  def error_501(error):
    return redirect(app.config['REDIRECT_URL_501'])

if 'REDIRECT_URL_502' in app.config:
  @app.errorhandler(502)
  def error_502(error):
    return redirect(app.config['REDIRECT_URL_502'])

if 'REDIRECT_URL_503' in app.config:
  @app.errorhandler(503)
  def error_503(error):
    return redirect(app.config['REDIRECT_URL_503'])
