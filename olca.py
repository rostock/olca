# -*- coding: utf-8 -*-

from flask import Flask, jsonify, redirect, request
from flask_compress import Compress
import openlocationcode as olc
import urllib



# initialise application
app = Flask(__name__)



# import configuration from file
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

# OLC handler
def olc_handler(x, y, query, epsg_in, epsg_out):

  # encode queried pair of coordinates if necessary, take query as the Plus code if not
  code = olc.encode(y, x) if query is None else query

  # take care of short Plus code if necessary
  code = code.split('+')[0].ljust(8, '0') + '+' if olc.isShort(code) else code
  
  # determine the level
  level = len(code.replace('+', '').rstrip('0')) / 2

  # decode the Plus code to calculate the center pair of coordinates and the bbox
  coord = olc.decode(code)
  center_x = coord.longitudeCenter
  center_y = coord.latitudeCenter
  bbox_sw_x = coord.longitudeLo
  bbox_sw_y = coord.latitudeLo
  bbox_ne_x = coord.longitudeHi
  bbox_ne_y = coord.latitudeHi

  # get the full Plus code
  code = olc.encode(center_y, center_x)

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

  # valid GeoJSON
  return {
    'type': 'Feature',
    'properties': {
      # longitude/x of the center pair of coordinates
      'center_x': center_x,
      # latitude/y of the center pair of coordinates
      'center_y': center_y,
      # grid level 1 code
      'code_level_1': olc.encode(center_y, center_x, 2),
      # grid level 2 code
      'code_level_2': olc.encode(center_y, center_x, 4),
      # grid level 3 code
      'code_level_3': olc.encode(center_y, center_x, 6),
      # grid level 4 code
      'code_level_4': olc.encode(center_y, center_x, 8),
      # grid level 5 code
      'code_level_5': code,
      # local code
      'code_local': code[4:],
      # short code (depending on the distance between the code center and the reference pair of coordinates)
      'code_short': olc.shorten(code, y, x) if query is None else olc.shorten(code, center_y, center_x),
      'epsg_in': epsg_in,
      'epsg_out': epsg_out,
      # grid level
      'level': level
    },
    'geometry': {
      'type': 'Polygon',
      'coordinates': bbox
    }
  }


# response handler
def response_handler(data, status):

  # always JSON
  response = jsonify(data)

  # CORS response header indicating whether the response can be shared with requesting code from the given origin:
  # set to corresponding value if provided in settings
  if 'ACCESS_CONTROL_ALLOW_ORIGIN' in app.config:
    response.headers['Access-Control-Allow-Origin'] = app.config['ACCESS_CONTROL_ALLOW_ORIGIN']
  return response, status




# routing
@app.route('/', methods=['GET', 'POST'])
def query():

  # globals

  # default error message
  message = 'value of required \'query\' parameter is neither a valid pair of coordinates (latitude/y, longitude/x) nor a valid Plus code'

  # default HTTP status code
  status = 400

  # request handling

  # required query parameter, i.e. what to look for:
  # set to corresponding value if provided via request arguments, return an error if not
  handled_request = request_handler(request, 'query')
  if handled_request is not None:
    # careful with the  the plus sign!
    query = urllib.unquote(urllib.quote_plus(handled_request))
  else:
    data = { 'message': 'missing required \'query\' parameter or parameter empty', 'status': status }
    return response_handler(data, status)

  # optional EPSG code parameter for queried pair of coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_in')
  if handled_request is not None:
    epsg_in = handled_request
  else:
    epsg_in = app.config['DEFAULT_EPSG_IN']

  # optional EPSG code parameter for returned pair of coordinates:
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
    data = { 'message': 'value of optional \'epsg_in\' parameter is not a number', 'status': status }
    return response_handler(data, status)

  # return an error if optional EPSG code parameter for returned coordinates is not a number
  try:
    epsg_out = int(epsg_out)
  except ValueError:
    data = { 'message': 'value of optional \'epsg_out\' parameter is not a number', 'status': status }
    return response_handler(data, status)

  # required query parameter, i.e. what to look for:
  # encode queried pair of coordinates if they are valid, return an error if not
  if ',' in query:
    query = query.split(',')
    try:
      data = olc_handler(float(query[1]), float(query[0]), None, epsg_in, epsg_out)
      return response_handler(data, 200)
    except:
      data = { 'message': message, 'status': status }
      return response_handler(data, status)
  # decode queried Plus code if it is valid, return an error if not
  else:
    try:
      data = olc_handler(None, None, query, epsg_in, epsg_out)
      return response_handler(data, 200)
    except:
      data = { 'message': message, 'status': status }
      return response_handler(data, status)



# custom error handling
@app.errorhandler(403)
def error_403(error):
  return redirect(app.config['REDIRECT_URL_403'])

@app.errorhandler(404)
def error_404(error):
  return redirect(app.config['REDIRECT_URL_404'])

@app.errorhandler(410)
def error_410(error):
  return redirect(app.config['REDIRECT_URL_410'])

@app.errorhandler(500)
def error_500(error):
  return redirect(app.config['REDIRECT_URL_500'])

@app.errorhandler(501)
def error_501(error):
  return redirect(app.config['REDIRECT_URL_501'])

@app.errorhandler(502)
def error_502(error):
  return redirect(app.config['REDIRECT_URL_502'])

@app.errorhandler(503)
def error_503(error):
  return redirect(app.config['REDIRECT_URL_503'])
