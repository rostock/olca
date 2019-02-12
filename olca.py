# -*- coding: utf-8 -*-
from flask import Flask, jsonify, redirect, request
from flask_compress import Compress
import openlocationcode as olc



# initialise application
app = Flask(__name__)



# import configuration from file
app.config.from_pyfile('settings.py', silent = True)



# initialise Compress
Compress(app)



# response handling
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

  # request handling

  # read incoming JSON data (just in case JSON data is provided via POST)
  request_data = request.get_json()
  # required query parameter, i.e. what to look for:
  # set to corresponding value if provided via request arguments, throw an error if not
  if request.method == 'GET' and 'query' in request.args:
    query = request.args['query']
  elif request.method == 'POST' and 'query' in request.form:
    query = request.form['query']
  elif request.method == 'POST' and request_data is not None and 'query' in request_data:
    query = request_data['query']
  else:
    status = 400
    data = { 'message': 'missing required \'query\' parameter or parameter empty', 'status': status }
    return response_handler(data, status)
  # optional EPSG code parameter for queried coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  if request.method == 'GET' and 'epsg_in' in request.args:
    epsg_in = request.args['epsg_in']
  elif request.method == 'POST' and 'epsg_in' in request.form:
    epsg_in = request.form['epsg_in']
  elif request.method == 'POST' and request_data is not None and 'epsg_in' in request_data:
    epsg_in = request_data['epsg_in']
  else:
    epsg_in = app.config['DEFAULT_EPSG_IN']
  # optional EPSG code parameter for returned coordinates:
  # set to corresponding value if provided via request arguments, set to corresponding default value in settings if not
  if request.method == 'GET' and 'epsg_out' in request.args:
    epsg_out = request.args['epsg_out']
  elif request.method == 'POST' and 'epsg_out' in request.form:
    epsg_out = request.form['epsg_out']
  elif request.method == 'POST' and request_data is not None and 'epsg_out' in request_data:
    epsg_out = request_data['epsg_out']
  else:
    epsg_out = app.config['DEFAULT_EPSG_OUT']
  
  # query processing
  
  # throw an error if optional EPSG code parameter for queried coordinates is not a number
  try:
    epsg_in = int(epsg_in)
  except ValueError:
    status = 400
    data = { 'message': 'value of optional \'epsg_in\' parameter is not a number', 'status': status }
    return response_handler(data, status)
  
  # throw an error if optional EPSG code parameter for returned coordinates is not a number
  try:
    epsg_out = int(epsg_out)
  except ValueError:
    status = 400
    data = { 'message': 'value of optional \'epsg_out\' parameter is not a number', 'status': status }
    return response_handler(data, status)

  status = 200
  data = { 'code': query, 'epsg_in': epsg_in, 'epsg_out': epsg_out }
  #code = olc.encode(-4.457458, 17.2424)
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
