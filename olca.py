# -*- coding: utf-8 -*-

from flask import Flask, jsonify, redirect, request
from flask_compress import Compress
from urllib import quote_plus, unquote
import openlocationcode as olc
import pyproj as p
import requests as req



# global constants
HTTP_OK_STATUS_ = 200
HTTP_ERROR_STATUS_ = 400
DEFAULT_ERROR_MESSAGE_ = 'value of required \'query\' parameter is neither a valid pair of coordinates (required order: longitude/x,latitude/y) nor a valid Plus code'
SEPARATOR_ = ','
OLC_EPSG_ = 4326
OLC_PRECISION_ = len(str(0.000125)[2:])



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
  
  # transform all pairs of coordinates to be returned if EPSG necessary, round to six decimals if not
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
      properties.update( { 'code_regional': municipality_reverse_handler(center_x, center_y, code_local) } )

  # valid GeoJSON
  return {
    'type': 'Feature',
    'properties': properties,
    'geometry': {
      'type': 'Polygon',
      'coordinates': bbox
    }
  }, HTTP_OK_STATUS_

# response handler
def response_handler(data, status):

  # always JSON
  response = jsonify(data)

  # CORS response header indicating whether the response can be shared with requesting code from the given origin:
  # set to corresponding value if provided in settings
  if 'ACCESS_CONTROL_ALLOW_ORIGIN' in app.config:
    response.headers['Access-Control-Allow-Origin'] = app.config['ACCESS_CONTROL_ALLOW_ORIGIN']
  return response, status

# municipality reverse search handler
def municipality_reverse_handler(x, y, code_local):

  # get URL of reverse geocoder returning municipality names (as GeoJSON) on querying pairs of coordinates from settings
  municipality_reverse_url = app.config['MUNICIPALITY_REVERSE_URL']

  # build the query string
  query = str(x) + ',' + str(y)

  # query the reverse geocoder, process the response and return the first municipality name found
  try:
    response = req.get(municipality_reverse_url + query).json()
    municipality_reverse_target_property = app.config['MUNICIPALITY_REVERSE_TARGET_PROPERTY']
    municipality_name = response['features'][0]['properties'][municipality_reverse_target_property]
    # drop the municipality name part after the comma if necessary
    municipality_name = municipality_name[:municipality_name.index(',')] if ',' in municipality_name else municipality_name
    return code_local + ', ' + municipality_name
  except:
    return 'not definable'

# municipality forward search handler
def municipality_forward_handler(municipality_name):

  # get URL of forward geocoder returning municipality centroids (as GeoJSON) on querying municipality names
  municipality_forward_url = app.config['MUNICIPALITY_FORWARD_URL']

  # query the forward geocoder, process the response and return the centroid pair of coordinates of the first municipality found
  try:
    response = req.get(municipality_forward_url + municipality_name).json()
    coordinates = response['features'][0]['geometry']['coordinates']
    return coordinates[0], coordinates[1]
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
    # careful with the  the plus sign!
    query = unquote(quote_plus(handled_request))
  else:
    data = { 'message': 'missing required \'query\' parameter or parameter empty', 'status': HTTP_ERROR_STATUS_ }
    return response_handler(data, HTTP_ERROR_STATUS_)

  # optional EPSG code parameter for queried pair of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_in')
  if handled_request is not None:
    epsg_in = handled_request
  else:
    epsg_in = app.config['DEFAULT_EPSG_IN']

  # optional EPSG code parameter for all returned pairs of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_out')
  if handled_request is not None:
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
