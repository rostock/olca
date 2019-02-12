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

        git clone https://github.com/rostock/OLCA /usr/local/olca/olca
        
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
