# OLCA – Open Location Code API

A web API for converting coordinates to [*Plus codes*](https://plus.codes) of the [*Open Location Code*](https://github.com/google/open-location-code) and vice versa – view it in production: https://geo.sv.rostock.de/olca

## Requirements

*   [*Python*](https://www.python.org)
*   [*Virtualenv*](https://virtualenv.pypa.io)
*   [*pip*](http://pip.pypa.io)

## Installation

1.  Create a new virtual *Python* environment, for example:

        virtualenv /usr/local/olca/virtualenv
        
1.  Clone the project:

        git clone https://github.com/rostock/olca /usr/local/olca/olca
        
1.  Activate the virtual *Python* environment:

        source /usr/local/olca/virtualenv/bin/activate
        
1.  Install the required *Python* modules via [*pip*](https://pip.pypa.io), the *Python* package management system:

        pip install -r requirements.txt

## Configuration

1.  Edit the general settings file `/usr/local/olca/olca/settings.py`

## Deployment

If you want to deploy OLCA with [*Apache HTTP Server*](https://httpd.apache.org) you have to make sure that [*mod_wsgi*](https://modwsgi.readthedocs.io) is installed, a module that provides a Web Server Gateway Interface (WSGI) compliant interface for hosting *Python* based web applications. Then, you can follow these steps:

1.  Create a new empty file `olca.wsgi`:

        touch /usr/local/olca/olca/olca.wsgi
        
1.  Open `olca.wsgi` and insert the following lines of code:
    
        import os
        activate_this = os.path.join('/usr/local/olca/virtualenv/bin/activate_this.py')
        with open(activate_this) as file_:
            exec(file_.read(), dict(__file__=activate_this))

        from olca import app as application

1.  Open your *Apache HTTP Server* configuration file and insert something like this:
    
        WSGIDaemonProcess    olca processes=4 threads=128 python-path=/usr/local/olca/olca:/usr/local/olca/virtualenv/lib/python2.7/site-packages
        WSGIProcessGroup     olca
        WSGIScriptAlias      /olca /usr/local/olca/olca/olca.wsgi process-group=olca
        
        <Directory /usr/local/olca/olca>
            Order deny,allow
            Require all granted
        </Directory>

## Usage

Provided that *OLCA* is running under `/olca`, the base URL of the API is `/olca/?`.

### Request methods

*OLCA* supports HTTP `GET` requests with all parameters passed in the query string. The API also supports HTTP `POST` requests with all parameters passed either via form data (i.e. `Content-Type: application/x-www-form-urlencoded`) or in a [JSON](https://www.json.org) body (i.e. `Content-Type: application/json`).

All HTTP request methods share the same parameter names. The parameter names and values are case-sensitive.

Example HTTP `GET` request:

        curl 'http://127.0.0.1/olca/?query=9F6J33VX+55&epsg_out=25833'

The same example as an HTTP `POST` request with form data:

        curl -X POST --data 'query=9F6J33VX+55&epsg_out=25833' http://127.0.0.1/olca/

The same example as an HTTP `POST` request with JSON body:

        curl -X POST -H 'Content-Type: application/json' --data '{ "query": "9F6J33VX+55", "epsg_out": 25833}' http://127.0.0.1/olca/

### Responses

*OLCA* always responds with a valid JSON document.

#### Error

A valid JSON document with `status` and `message` is returned in case of any error. The `status` is identical to the returned HTTP status.

Example HTTP `GET` request with missing parameter:

        curl 'http://127.0.0.1/olca/?epsg_out=25833'

And the corresponding JSON response:

        {
          "message": "missing required 'query' parameter or parameter empty",
          "status": 400
        }

#### Success

Successful requests result in a valid [GeoJSON](http://geojson.org) document with exactly one `Feature` containing properties and a geometry of type `Polygon`.

Example successful HTTP `POST` request with JSON body:

        curl -X POST -H 'Content-Type: application/json' --data '{ "query": "5997753,310224", "epsg_in": 25833, "epsg_out": 2398}' http://127.0.0.1/olca/

And the corresponding GeoJSON response:

        {
          "geometry": {
            "coordinates": [
              [
                [
                  4506527.742360309,
                  5996406.554493488
                ],
                [
                  4506535.901855983,
                  5996406.554493488
                ],
                [
                  4506535.901855983,
                  5996420.479254515
                ],
                [
                  4506527.742360309,
                  5996420.479254515
                ],
                [
                  4506527.742360309,
                  5996406.554493488
                ]
              ]
            ],
            "type": "Polygon"
          },
          "properties": {
            "center_x": 4506531.822114297,
            "center_y": 5996413.516872162,
            "code_level_1": "9F000000+",
            "code_level_2": "9F6J0000+",
            "code_level_3": "9F6J3300+",
            "code_level_4": "9F6J33VX+",
            "code_level_5": "9F6J33VX+55",
            "code_local": "33VX+55",
            "code_short": "+55",
            "epsg_in": 25833,
            "epsg_out": 2398,
            "level": 5
          },
          "type": "Feature"
        }

### Parameters

The following parameters are valid for all requests:

| Name | Example(s) | Description | Required | Default |
| --- | --- | --- | --- | --- |
| `query` | `9F6J33VX+55` or `9F6J33+` or `9F000000+` or `54.092,12.098` or `5997644,310223` | the query string: either a valid pair of coordinates (**required order**: latitude/y,longitude/x) or a valid *Plus code* | yes | / |
| `epsg_in` | `4326` or `25833` | the [EPSG code](http://www.epsg.org) for all returned pairs of coordinates | no | as configured in `settings.py` |
| `epsg_out` | `25833` or `2398` | the EPSG code for all returned pairs of coordinates | no | as configured in `settings.py` |

### Cross-Origin Resource Sharing

By default, browsers, for security reasons, do not allow making API calls to a different domain.

Depending on the configuration in `settings.py`, *OLCA* sends an `Access-Control-Allow-Origin: '*'` header with each response to allow this Cross-Origin Resource Sharing. This header is [supported by most browsers](https://caniuse.com/#search=cors).