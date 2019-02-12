# -*- coding: utf-8 -*-

from featurecollection import FeatureCollection
from flask import Flask, jsonify, redirect, request
from flask_compress import Compress
import openlocationcode as olc



# initialise application
app = Flask(__name__)



# import configuration from file
app.config.from_pyfile('settings.py', silent = True)



# initialise Compress
Compress(app)



# custom classes

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



# custom functions

# request handler
def request_handler(request, arg_name):
  # read JSON data (just in case JSON data is provided via POST)
  request_data = request.get_json()
  
  # cover GET method, POST method with form body and POST method with JSON data
  if request.method == 'GET' and arg_name in request.args:
    return request.args[arg_name]
  elif request.method == 'POST' and arg_name in request.form:
    return request.form[arg_name]
  elif request.method == 'POST' and request_data is not None and arg_name in request_data:
    return request_data[arg_name]
  
# OLC handler
def olc_handler(code):
  # decode the full Plus code (again)
  coord = olc.decode(code)
  return {
    # longitude/x of the center pair of coordinates
    'x': coord.longitudeCenter,
    # latitude/y of the center pair of coordinates
    'y': coord.latitudeCenter,
    # local code
    'code_local': code[4:],
    # grid level 0 code
    'level_0': code[:2],
    # grid level 1 code
    'level_1': code[:4],
    # grid level 2 code
    'level_2': code[:6],
    # grid level 3 code
    'level_3': code[:9]
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
    query = handled_request
  else:
    data = { 'message': 'missing required \'query\' parameter or parameter empty', 'status': status }
    return response_handler(data, status)

  # optional EPSG code parameter for queried coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_in')
  if handled_request is not None:
    epsg_in = handled_request
  else:
    epsg_in = app.config['DEFAULT_EPSG_IN']

  # optional EPSG code parameter for returned coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  handled_request = request_handler(request, 'epsg_out')
  if handled_request is not None:
    epsg_out = handled_request
  else:
    epsg_out = app.config['DEFAULT_EPSG_OUT']
  
  # query processing
  
  # return an error if optional EPSG code parameter for queried coordinates is not a number
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
  # encode queried coordinates if they are valid, return an error if not
  if ',' in query:
    query = query.split(',')
    try:
      x = float(query[1])
      y = float(query[0])
      code = olc.encode(y, x)
      olc_data = olc_handler(code)
    except:
      data = { 'message': message, 'status': status }
      return response_handler(data, status)
  # decode queried Plus code if it is valid, return an error if not
  else:
    try:
      # handle the plus sign correctly
      code = query.replace(' ', '+')
      olc_data = olc_handler(code)
    except:
      data = { 'message': message, 'status': status }
      return response_handler(data, status)

  # default return behaviour if everything is going well
  status = 200
  default_data = { 'code': code, 'epsg_in': epsg_in, 'epsg_out': epsg_out }
  data = dict(default_data.items() + olc_data.items())
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
